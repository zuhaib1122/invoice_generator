from datetime import date
import streamlit as st
import pandas as pd
import io

# page configuration
st.set_page_config(page_title='Stationary Data Form')

# state initialization 
if "page" not in  st.session_state:
    st.session_state["page"] = "input"

if "invoice_items" not in st.session_state:
    st.session_state["invoice_items"] = []

# get the current date
today = date.today()
#correct date format
today_string = today.strftime("%d-%m-%Y")  
#correct the invoice number
auto_id = f"INV{today.strftime("%Y%m%d")}"
if "invoice_meta" not in st.session_state:
    st.session_state["invoice_meta"] = {
        "customer_name": "",
        "invoice_no": auto_id,
        "date": today_string
    }
else:
    # repair the old date and invoice number while keeping the customer's name
    st.session_state["invoice_meta"]["invoice_no"] = auto_id
    st.session_state["invoice_meta"]["date"] = today_string
# empty table warrning dialog 
@st.dialog("⚠️ Action Required")
def show_empty_warning():
    st.error("The invoice table is empty. Please add at least one item before generating invoice.")

    if st.button('Got it', type='primary'):
        st.rerun()


# report lab / pdf import
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )

    PDF_AVAILABLE = True

except ImportError:
    PDF_AVAILABLE = False


# GENERATE PDF
def generate_pdf_bytes():
    # generate professional invoice in memory
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []
    styles = getSampleStyleSheet()

    # Style for company name and left header detail
    company_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1E3A8A"),
        leading=20
    )

    # Left column text containing name, caption, phone, and invoice title
    left_header_text = (
        "<b>APEX STATIONERY SUPPLIERS</b><br/>"
        "Wholesale Supplier of Office & School Stationery Parts<br/>"
        "Phone: +92 300 1234567<br/><br/>"
        "<b>INVOICE</b>"
    )

    # Create style for right-side metadata
    meta_style = ParagraphStyle(
        "invoice_meta",
        parent=styles["Normal"],
        fontSize=12,
        leading=15
    )

    # Group the three metadata values together
    right_box_text = (
        f"Invoice # {st.session_state.invoice_meta['invoice_no']}<br/>"
        f"Date: {st.session_state.invoice_meta['date']}<br/>"
        f"Name: {st.session_state.invoice_meta['customer_name']}"
    )

    # Create 1 row and 2 columns data structure
    header_data = [[
        Paragraph(left_header_text, company_style),
        Paragraph(right_box_text, meta_style)
    ]]

    header_table = Table(
        header_data,
        colWidths=[300, 240]
    )

    # Apply styling
    header_table.setStyle(TableStyle([
        # Vertically align both sides
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # Border around right cell
        ("BOX", (1, 0), (1, 0), 1, colors.HexColor("#1E3A8A")),

        # Light background inside right box
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F9FAFB")),

        # Padding inside right box
        ("TOPPADDING", (1, 0), (1, 0), 8),
        ("BOTTOMPADDING", (1, 0), (1, 0), 8),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("RIGHTPADDING", (1, 0), (1, 0), 10),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # Table data
    table_data = [
        ["Item", "Quantity", "Unit Price", "Total Price"]
    ]

    subtotal = 0.0

    for item in st.session_state.invoice_items:
        total = item["Quantity"] * item["Unit Price"]
        subtotal += total

        table_data.append([
            item["Item Name"],
            str(item["Quantity"]),
            f"Rs. {item['Unit Price']:,.2f}",
            f"Rs. {total:,.2f}"
        ])

    # Grand total row
    table_data.append([
        "",
        "",
        "Grand Total:",
        f"Rs. {subtotal:,.2f}"
    ])

    # Create PDF table
    table = Table(
        table_data,
        colWidths=[250, 80, 100, 110]
    )

    table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),

        # Alignment
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),

        # Body
        ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#F9FAFB")),

        # Grid
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#E5E7EB")),

        # Grand total
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#1E3A8A")),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, -1), (-1, -1), 8),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)

    buffer.seek(0)

    return buffer.getvalue()
# page 1, invoice builder
if st.session_state["page"] == "input":
    st.title('invoice Builder & Generator')
    st.divider()
    # generate left and right columns
    left_col, right_col = st.columns([1,2], gap='large')
    # left column
    with left_col:
        st.subheader('Data Required')
        invoice_no = st.info(f"Invoice # {st.session_state['invoice_meta']['invoice_no']}")
        invoice_date = st.info(f"Date: {st.session_state['invoice_meta']['date']}")
        customer_name = st.text_input("Customer Name", value=st.session_state["invoice_meta"]["customer_name"])
        # update invice meta
        st.session_state["invoice_meta"]["customer_name"] = customer_name
        with st.form("Item_entry_form", clear_on_submit=True):
            item_name = st.selectbox("Select Product", ['Pencil', 'Rubber', 'Shopner', 'Stepler'])
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1, format="%d")
            unit_price = st.number_input("Unit Price (PKR)", min_value=0.0, value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add to table", use_container_width=True)
        # add to table
        if submitted:
            if not item_name:
                st.warning('Please select the valid item from the list')
            else:
                st.session_state["invoice_items"].append(
                    {
                        "Item Name": item_name,
                        "Quantity": int(quantity),
                        "Unit Price": float(unit_price),
                        "Total Price": float(quantity * unit_price)
                    }
                )
                st.success(f"Added '{item_name}' to table")
                st.rerun()

    # right column
    with right_col:
        st.subheader("Selected products")
        with st.container(border=True):
            #check if there are any items added to the invoice
            if st.session_state.get("invoice_items"):
                # running subtotal to display on screen
                running_subtotal = 0.0
                # loop through each item with their index
                for i, item in enumerate(st.session_state["invoice_items"]):
                    item_total = item["Quantity"] * item["Unit Price"]
                    running_subtotal+=item_total
                    # create layout columns for each row
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    with col1:
                        st.write(f"**{item["Item Name"]}")
                    with col2:
                        st.write(f"Qty {item["Quantity"]}")
                    with col3:
                        st.write(f"Rs {item["Unit Price"]:,.2f}")
                    with col4:
                        st.write(f"Rs {item_total:,.2f}")
                    with col5:
                        # unique key for each button using 'i'
                        if st.button("❌", key=f"delete_item_{i} "):
                            # remove the item fom session by is index
                            st.session_state["invoice_items"].pop(i)
                            # instantly rerun app
                            st.rerun()
                st.markdown(f"### Subtotal: Rs. {running_subtotal:,.2f}")
            else:
                st.info("No item selected yet")
        # generate invoice button
        if st.button("Generate Invoice", type="primary", use_container_width=True):
            if len(st.session_state["invoice_items"]) == 0:
                show_empty_warning()
            else:
                st.session_state["page"] = 'invoice'
                st.rerun()
# professional invoice view
elif st.session_state["page"] == 'invoice':
    
    # at the top left side header and right side invoice info
    col1, col2, col3 = st.columns([1,4,2])
    with col1:
        # back button
        if st.button("⬅️", use_container_width=True):
                st.session_state["page"] = 'input'
            
    with col2:
        st.markdown("# **APEX STATIONERY SUPPLIERS**")
    with col3:
        with st.container(border=True):
            st.write(f"Invoice # {st.session_state["invoice_meta"]["invoice_no"]}")
            st.write(f"Date: {st.session_state['invoice_meta']['date']}")
            st.write(f"Name: {st.session_state["invoice_meta"]['customer_name']}")
    # information about the products order
    cola, colb = st.columns([5,2])
    with cola:
        col1, col2, col3, col4 = st.columns([4,1,1,1])
        with col1:
            st.markdown('**Product**')
        with col2:
            st.markdown('**Qty**')
        with col3:
            st.markdown('**Unit Price**')
        with col4:
            st.markdown('**Total Price**')
    running_subtotal = 0.0
    # loop through each item with their index
    for i, item in enumerate(st.session_state["invoice_items"]):
        item_total = item["Quantity"] * item["Unit Price"]
        running_subtotal+=item_total
    # create layout columns for each row
        with col1:
            st.write(f"**{item["Item Name"]}")
        with col2:
            st.write(f"{item["Quantity"]}")
        with col3:
            st.write(f"Rs {item["Unit Price"]}")
        with col4:
            st.write(f"Rs {item_total}")
                    
    with colb:
        with st.container(border=True):
            st.markdown(f"## **SubTotal**" 
                        f"Rs {running_subtotal}")
    # try to make the download button at center 
    col1, col2, col3 = st.columns([2, 2, 2])
    with col3:
        if PDF_AVAILABLE:
            pdf_data = generate_pdf_bytes()
            st.download_button(label='Download PDF', data=pdf_data, file_name=(f"{st.session_state['invoice_meta']['customer_name']}.pdf"), mime="application/pdf", type="primary", use_container_width=True)
        else:
            st.warning("PDF download library (reportlab) is not installed. ")
