from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput

def generate_letter(dispute_type, tenant_name='', landlord_name='', address='', issue_desc='', amount=''):
    # Templates for 3 common rental disputes
    templates = {
        "repair_request": f"""
        Dear {landlord_name or 'Landlord'},

        Please arrange repairs at {address or '[Property Address]'} for this issue:
        {issue_desc or '[Repair details]'}.

        Thanks,
        {tenant_name or '[Your Name]'}
        """,
        "deposit_claim": f"""
        Dear {landlord_name or 'Landlord'},

        I request the return of my security deposit ({amount or '[Amount]'}) for {address or '[Property Address]'}.
        Please provide any deductions.

        Thanks,
        {tenant_name or '[Your Name]'}
        """,
        "rent_increase_dispute": f"""
        Dear {landlord_name or 'Landlord'},

        I dispute the rent increase of {amount or '[Amount]'} for {address or '[Property Address]'}.
        Please provide documentation supporting this change.

        Thanks,
        {tenant_name or '[Your Name]'}
        """
    }
    return templates.get(dispute_type.lower(), "Invalid dispute type. Use: repair_request, deposit_claim, rent_increase_dispute.")

def dispute_tool(params):
    letter = generate_letter(
        params.get('dispute_type', ''),
        params.get('tenant_name', ''),
        params.get('landlord_name', ''),
        params.get('property_address', ''),
        params.get('issue_description', ''),
        params.get('claim_amount', '')
    )
    return ToolOutput(
        tool="dispute_tool",
        input=params,
        output=letter,
        step="Generate dispute resolution letter"
    )

dispute_resolution_tool = StructuredTool.from_function(
    func=dispute_tool,
    name="dispute_resolution_tool",
    description="Generates letters for common rental disputes: repair requests, deposit returns, rent increase disputes."
)