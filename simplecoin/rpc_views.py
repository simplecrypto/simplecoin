import six
import sys
import sqlalchemy

from flask import current_app, request, abort, Blueprint, g
from functools import wraps
from itsdangerous import TimedSerializer, BadData

from .models import Transaction, Payout, BonusPayout, TransactionSummary
from .utils import Benchmark
from .views import main
from . import db


rpc_views = Blueprint('rpc_views', __name__)


@rpc_views.errorhandler(Exception)
def api_error_handler(exc):
    try:
        six.reraise(type(exc), exc, tb=sys.exc_info()[2])
    except Exception:
        current_app.logger.error("Unhandled exception encountered in rpc view", exc_info=True)
    resp = dict(result=False)
    return sign(resp, 500)


def sign(data, code=200):
    serialized = g.signer.dumps(data)
    return serialized


@rpc_views.before_request
def check_signature():
    g.signer = TimedSerializer(current_app.config['rpc_signature'])
    try:
        g.signed = g.signer.loads(request.data)
    except BadData:
        abort(403)


@rpc_views.route("/get_payouts", methods=['POST'])
def get_payouts():
    """ Used by remote procedure call to retrieve a list of transactions to
    be processed. Transaction information is signed for safety. """
    current_app.logger.info("get_payouts being called, args of {}!".format(g.signed))
    merged = g.signed['currency']
    if merged == current_app.config['currency']:
        merged = None

    with Benchmark("Fetching payout information"):
        pids = [(p.user, p.amount, "P{}".format(p.id)) for p in Payout.query.filter_by(transaction_id=None, merged_type=merged).
                join(Payout.block, aliased=True).filter_by(mature=True)]
        bids = [(p.user, p.amount, "B{}".format(p.id)) for p in BonusPayout.query.filter_by(transaction_id=None, merged_type=merged).
                join(BonusPayout.block, aliased=True).filter_by(mature=True)]
    return sign(dict(pids=pids + bids))


@rpc_views.route("/update_payouts", methods=['POST'])
def update_transactions():
    """ Used as a response from an rpc payout system. This will either reset
    the locked status of a list of transactions upon failure on the remote
    side, or create a new CoinTransaction object and link it to the
    transactions to signify that the transaction has been processed. Both
    request and response are signed. """
    # basic checking of input
    try:
        if 'coin_txid' in g.signed:
            assert len(g.signed['coin_txid']) == 64
        else:
            assert 'reset' in g.signed
            assert isinstance(g.signed['reset'], bool)
        assert isinstance(g.signed['pids'], list)

        # A bit of a messy hack to split payout ids into bonus and regular
        # payouts
        g.signed['all_pids'] = g.signed['pids']
        g.signed['pids'] = []
        g.signed['bids'] = []
        for id in g.signed['all_pids']:
            if id[0] == "P":
                g.signed['pids'].append(int(id[1:]))
            elif id[0] == "B":
                g.signed['bids'].append(int(id[1:]))
            else:
                raise Exception("Invalid payout id prefix!")

    except (AssertionError, Exception):
        current_app.logger.warn("Invalid data passed to confirm", exc_info=True)
        abort(400)

    if 'coin_txid' in g.signed:
        with Benchmark("Associating payout transaction ids"):
            merged_type = g.signed['currency']
            if merged_type == current_app.config['currency']:
                merged = None

            try:
                coin_trans = Transaction.create(g.signed['coin_txid'], merged_type=merged_type)
                db.session.flush()
            except sqlalchemy.exc.IntegrityError:
                db.session.rollback()
                current_app.logger.warn("Transaction id {} already exists!"
                                        .format(g.signed['coin_txid']))
            user_amounts = {}
            user_counts = {}
            for payout in Payout.query.filter(Payout.id.in_(g.signed['pids'])):
                user_counts.setdefault(payout.user, 0)
                user_amounts.setdefault(payout.user, 0)
                user_amounts[payout.user] += payout.amount
                user_counts[payout.user] += 1

            for payout in BonusPayout.query.filter(BonusPayout.id.in_(g.signed['bids'])):
                user_counts.setdefault(payout.user, 0)
                user_amounts.setdefault(payout.user, 0)
                user_amounts[payout.user] += payout.amount
                user_counts[payout.user] += 1

            for user in user_counts:
                TransactionSummary.create(
                    g.signed['coin_txid'], user, user_amounts[user], user_counts[user])

            if g.signed['pids']:
                Payout.query.filter(Payout.id.in_(g.signed['pids'])).update(
                    {Payout.transaction_id: g.signed['coin_txid']}, synchronize_session=False)
            if g.signed['bids']:
                BonusPayout.query.filter(BonusPayout.id.in_(g.signed['bids'])).update(
                    {BonusPayout.transaction_id: g.signed['coin_txid']}, synchronize_session=False)

            db.session.commit()

    return sign(dict(result=True))


@rpc_views.route("/confirm_transactions", methods=['POST'])
def confirm_transactions():
    """ Used to confirm that a transaction is now complete on the network. """
    # basic checking of input
    try:
        if 'tids' in g.signed:
            assert isinstance(g.signed['tids'], list)
        if 'fees' in g.signed:
            assert isinstance(g.signed['fees'], dict)
    except AssertionError:
        current_app.logger.warn("Invalid data passed to confirm_transactions",
                                exc_info=True)
        abort(400)
    txdata = {}
    for txid, fee in g.signed['fees'].iteritems():
        txdata.setdefault(txid, {})
        txdata[txid][Transaction.fee] = fee

    for txid in g.signed['tids']:
        txdata.setdefault(txid, {})
        txdata[txid][Transaction.confirmed] = True

    for txid in txdata:
        Transaction.query.filter(Transaction.txid.in_(txid)).update(
            txdata[txid], synchronize_session=False)
    db.session.commit()
    return sign(dict(result=True))
