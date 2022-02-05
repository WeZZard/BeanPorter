# BeanPorter - A Standalone Configurable BeanCount Importer

## Setup

Install via pip

```bash
pip install BeanPorter
```

Install via pipenv

```bash
pipenv install BeanPorter
```

## Usage

Import with default rules to beancount file `BEANCOUNT_FILE.beancount`.

```bash
bean-porter --file BILL_FILE.csv \
  >> BEANCOUNT_FILE.beancount
```

Import with custom rules which were written in `CONFIG_FILE.yaml`.

```bash
bean-porter --config CONFIG_FILE.yaml \
  --file BILL_FILE.csv \
  >> BEANCOUNT_FILE.beancount
```

> By default, `BILL_FILE` can only start with "微信支付账单" or "alipay_record.".

## Configure

You can configure BeanPorter with BeanPorter Configure Markup Language (BPCML).
BPCML is a domain specific language extended from YAML which helps reduce 
workload of building rules for importing different bills.

## Contribut to the Project

BeanPorter is envolved from Beancount-CSVImporter done by Shangyan Zhou (aka
Sphish) -- Though current design of the project is totally different from
the original one, but the original project's codes help me a lot understand
how bean-extract works, and shows a result of thinking of configurable
Beancount bills import program.

Currently, this project is not perfect. There is no diagnostic engine to help
user find out erroneous in its configuration. At the same time, you may spot
there are other points can be improved. Any contribution to the project is
welcome.

### Develop with VSCode

You may fill the following contents to your VSCode's `settings.json` to help
`python unittest` to discover and run test cases.

```
{
  "python.testing.unittestArgs": [
    "-v",
    "-s",
    "${workspaceFolder}/tests",
    "-p",
    "*Tests.py",
  ],
  "python.testing.pytestEnabled": false,
  "python.testing.unittestEnabled": true,
  "python.testing.cwd": "${workspaceFolder}/src",
}
```

## License

MIT

## Understanding BPCML

TODO: enrich this section

## BPCML Language Manual

BPCML is extended from YAML. The differences between BPCML and YAML is that
there are special secions which instructs BeanPorter to build importing rules.

TODO: enrich this section

## An Example BPCML File

```yaml
disabled_importers:
  - Alipay
  - WeChatPay
```

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