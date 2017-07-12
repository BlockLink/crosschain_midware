db.createCollection("s_user");
db.createCollection("b_chain_info");
db.createCollection("b_block");
db.createCollection("b_raw_transaction");
db.createCollection("b_raw_transaction_input");
db.createCollection("b_raw_transaction_output");
db.createCollection("b_chain_account");
db.createCollection("b_deposit_transaction");
db.createCollection("b_withdraw_transaction");
db.createCollection("s_configuration");
db.createCollection("b_cash_sweep");
db.createCollection("b_cash_sweep_plan_detail")

db.b_chain_account.ensureIndex({"chainId":1, "address": 1}, {"unique":true});
db.s_user.ensureIndex({'email': 1}, {"unique":true});
db.s_user.ensureIndex({'username': 1}, {"unique":true});
db.b_block.ensureIndex({'chainId': 1});
db.b_block.ensureIndex({'blockHash': 1});
db.b_raw_transaction.ensureIndex({'chainId': 1});
db.b_raw_transaction.ensureIndex({'trxId': 1});
db.b_raw_transaction_input.ensureIndex({'rawTransactionid': 1});
db.b_raw_transaction_input.ensureIndex({'address': 1});
db.b_raw_transaction_output.ensureIndex({'rawTransactionid': 1});
db.b_raw_transaction_output.ensureIndex({'address': 1});
db.b_chain_account.ensureIndex({'name': 1});
db.b_chain_account.ensureIndex({'address': 1});
db.b_chain_account.ensureIndex({'chainId': 1});
db.b_chain_account.ensureIndex({'creatorUserId': 1});
db.b_chain_account.ensureIndex({'chainId': 1, 'address': 1}, {'unique': true});
db.b_deposit_transaction.ensureIndex({'chainId': 1});
db.b_deposit_transaction.ensureIndex({'fromAddress': 1});
db.b_withdraw_transaction.ensureIndex({'chainId': 1});
db.b_withdraw_transaction.ensureIndex({'toAddress': 1});
db.b_config.ensureIndex({'key': 1}, {'unique': true});

db.b_config.insert({
    'key': 'cash_sweep_address',
    'value': [
        {
            'chainId': 'eth',
            'address': '0x1234'
        },
        {
            'chainId': 'btc',
            'address': 'adf892fg'
        }
    ]
})
