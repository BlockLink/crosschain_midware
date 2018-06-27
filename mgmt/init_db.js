db = db.getSiblingDB('admin')
if (db.auth("dbAdmin", "admin12#$%") != 1) {
    db.createUser(
        {
            user: "dbAdmin",
            pwd: "admin12#$%",
            roles: [{role: "root", db: "admin"}]
        }
    )
    db.auth("dbAdmin", "admin12#$%")
    db = db.getSiblingDB('chaindb')
    db.createUser(
        {
            user: "chaindb_user",
            pwd: "yqr.1010",
            roles: [{role: "readWrite", db: "chaindb"}]
        }
    )
    db.auth("chaindb_user", "yqr.1010")

    db.createCollection("s_user");
    db.createCollection("b_chain_info");
    db.createCollection("b_block");
    db.createCollection("b_raw_transaction");
    db.createCollection("b_raw_transaction_input");
    db.createCollection("b_raw_transaction_output");
    db.createCollection("b_chain_account");
    db.createCollection("b_btc_unspent");
    db.createCollection("b_btc_multisig_address");
    db.createCollection("b_deposit_transaction");
    db.createCollection("b_withdraw_transaction");
    db.createCollection("b_exchange_contracts");
    db.createCollection("b_fee_providers");
    db.createCollection("b_balance_unspent")
    db.createCollection("b_balance_spent")
    db.b_chain_account.ensureIndex({"chainId": 1, "address": 1}, {"unique": true});
    db.b_balance_unspent.ensureIndex({"chainId": 1, "address": 2});
    db.b_balance_spent.ensureIndex({"chainId": 1, "address": 2});
    db.s_user.ensureIndex({'email': 1}, {"unique": true});
    db.s_user.ensureIndex({'username': 1}, {"unique": true});
    db.b_block.ensureIndex({'chainId': 1});
    db.b_block.ensureIndex({'blockHash': 1});
    db.b_block.ensureIndex({'blockNumber':1});
    db.b_block.ensureIndex({'blockNumber':1, "chainId": 1});
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
        'key': 'syncblocknum',
        'value': '4000000'
    });
    db.b_config.insert({
        'key': 'safeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'syncstate',
        'value': 'false'
    });
    db.b_config.insert({
        'key': 'btcsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'btcsafeblock',
        'value': '2'
    });
    db.b_config.insert({
        'key': 'btcsyncstate',
        'value': 'false'
    });
    db.b_config.insert({
        'key': 'ltcsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'ltcsafeblock',
        'value': '2'
    });
    db.b_config.insert({
        'key': 'ltcsyncstate',
        'value': 'false'
    });
     db.b_config.insert({
        'key': 'ubsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'ubsafeblock',
        'value': '2'
    });
    db.b_config.insert({
        'key': 'ubsyncstate',
        'value': 'false'
    });
     db.b_config.insert({
        'key': 'hcsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'hcsafeblock',
        'value': '2'
    });
    db.b_config.insert({
        'key': 'hcsyncstate',
        'value': 'false'
    });
    db.b_config.insert({
        'key': 'etpsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'etpsafeblock',
        'value': '2'
    });


}

