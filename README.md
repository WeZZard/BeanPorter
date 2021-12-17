# Usage

```bash
bean-extract config.py 微信支付账单_xxx.csv/alipay_record_xxx.csv > xxxxxxx.bean
```

**Notice:The raw data filename can only start with "微信支付账单" or "alipay_record."**

```yaml
developer:
  debug: true
disabled_importers:
  - Alipay
  - WeChatPay
include: # include list, import as root configurations
  - xxx.yaml
importers:
  -
    name: WeChatPay
    probe:
      file_name:
        pattern: xxx # Regex is supported
        # or use "prefix: xxx", Regex is not supported
        # or use "suffix: xxx", Regex is not supported
    strippers:
      remove_first: 4
      remove_last: 10
      remove_before: "xxx" # Regex is allowed
      remove_after: "xxx" # Regex is allowed
      remove_before_and_include: "xxx" # Regex is allowed
      remove_after_and_include: "xxx" # Regex is allowed
    variables:
      交易時間: timestamp
    transformers:
      -
        patterns:
        results:
          debit_currency: "CNY"
          credit_currency: "CNY"
      - 
      -
        patterns:
					payee:
        results:
          debit_currency: "CNY"
          credit_currency: "CNY"
      - 
        name: ""
        patterns:
          payee: 全家
          category: 商戶消費
          good: ...
          drcr: 支出 # debit, credit or unspecified
          account: 招商銀行(xxxx) # 餘額寶，花唄
          status: 交易成功 # 使用平臺原始文本
          amount: # Internal usage
          timestamp: # Internal usage
          system_txn_id: # Internal usage
          vendor_txn_id: # Internal usage
          交易類型: # 使用平臺原始文本
        results:
          payee: $objective # $xxx is a variable derived from terminologies
          transaction_name: $good
          date: $date
          time: $time
          debit_account: XXX
          debit_amount: XXX
          debit_currency: XXX
          debit_price: XXX
          debit_cost: XXX
          credit_account: XXX
          credit_amount: XXX
          credit_currency: XXX
          credit_price: XXX
          credit_cost: XXX
extensions: # Only allows to extend importers
  -
    name: WeChat
    transformers:
      -
        # ...
extends_WeChat: # Only allows to extend specific importer
  transformers:
    -
      # ...
```