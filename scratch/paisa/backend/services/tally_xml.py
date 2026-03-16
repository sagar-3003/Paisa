def build_sales_voucher(entry: dict, gst: dict) -> str:
    """Build Tally-compatible XML for a sales entry."""
    # Assuming standard date format 'YYYY-MM-DD'
    date = str(entry.get("date", "")).replace("-", "")  # Tally format: YYYYMMDD
    if not date:
        date = "20260316" # fallback to current if missing

    # CGST+SGST scenario
    ledger_entries = f"""
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{entry.get('party_name', 'Cash')}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{gst.get('total_amount', entry.get('total_amount', 0))}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Sales Account</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{entry.get('total_amount', 0)}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Output CGST</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{gst.get('taxes', {{}}).get('CGST', 0)}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>
        <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Output SGST</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{gst.get('taxes', {{}}).get('SGST', 0)}</AMOUNT>
        </ALLLEDGERENTRIES.LIST>
    """

    return f"""
    <ENVELOPE>
      <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
      </HEADER>
      <BODY>
        <IMPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>Vouchers</REPORTNAME>
            <STATICVARIABLES>
              <SVCURRENTCOMPANY>##SVCURRENTCOMPANY</SVCURRENTCOMPANY>
            </STATICVARIABLES>
          </REQUESTDESC>
          <REQUESTDATA>
            <TALLYMESSAGE xmlns:UDF="TallyUDF">
              <VOUCHER VCHTYPE="Sales" ACTION="Create">
                <DATE>{date}</DATE>
                <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                <PARTYLEDGERNAME>{entry.get('party_name', 'Cash')}</PARTYLEDGERNAME>
                <NARRATION>{entry.get('notes', 'Entry via Paisa AI')}</NARRATION>
                {ledger_entries}
              </VOUCHER>
            </TALLYMESSAGE>
          </REQUESTDATA>
        </IMPORTDATA>
      </BODY>
    </ENVELOPE>
    """

# In a real app we'd also implement `build_purchase_voucher`, `build_journal_voucher`, etc.
