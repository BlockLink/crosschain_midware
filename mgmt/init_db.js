conn = new Mongo();
db = conn.getDB("chaindb");

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
