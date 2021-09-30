# -- Import -- #
import sys
import os
import re
from subprocess import check_call


# -- Constants -- #
PDF_TO_TEXT_PATH = r'C:\tools\gnuwin32\bin\pdftotext.EXE'
PDF_TO_TEXT_ARGS = ['-layout', '-table', '-nopgbrk', '-bom']
EXTRA_WHITESPACE_PATTERN = re.compile(r'\s{2,}')
DISALLOWED_CHARS_PATTERN = re.compile(r'["]')
RESTAURANT_NAME_PATTERN = re.compile(
    r'(Your order from (.+?) is +being +prepared|Thanks for your (.+?) order)')
DATE_PATTERN = re.compile(
    r'Grubhub <orders@eat.grubhub.com> + (Mon|Tues|Wed|Thu|Fri|Sat|Sun), ((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).+?) at \d')
LINE_ITEM_PATTERN = re.compile(r'\s*(\d)\s+([A-Za-z &\-*.]+)\s+\$(\d+\.\d+)$')
FEE_ITEM_PATTERN = re.compile(r'(Delivery +fee|Sales +tax|Service +fee|Tip)\s+\$(\d+\.\d+)$')


# -- Main -- #
def main():

    if os.path.isdir(sys.argv[1]):
        convert_pdfs(sys.argv[1])

        all_data_rows = []
        for thing in os.listdir(sys.argv[1]):
            if thing.lower().endswith('.txt'):
                # print()
                all_data_rows.extend(parse_text(os.path.join(sys.argv[1], thing)))
        
        if all_data_rows:
            export_csv(os.path.dirname(sys.argv[1]) + '.csv', ['"Restaurant","Item","Category","Order Date","Purchased By"'] + all_data_rows)

    return


def clean_text(some_string):
    if not some_string:
        return ''
    some_string = re.sub(DISALLOWED_CHARS_PATTERN, ' ', some_string.strip())
    some_string = re.sub(EXTRA_WHITESPACE_PATTERN, ' ', some_string.strip())
    return some_string


def parse_text(some_text_path):
    # print('\t>' + some_text_path) # DEBUG
    data_rows = []
    with open(some_text_path, 'r') as txtfile:
        restaurant_name = None
        order_date = None
        for line in txtfile.readlines():
            output_row = ''
            if not restaurant_name:
                is_rname = RESTAURANT_NAME_PATTERN.match(line)
                if is_rname and is_rname.group(3):
                    restaurant_name = is_rname.group(3)
                elif is_rname:
                    restaurant_name = is_rname.group(2)

            if not order_date:
                is_date = DATE_PATTERN.match(line)
                if is_date:
                    order_date = is_date.group(2)

            if '$' in line:
                is_line_item = LINE_ITEM_PATTERN.match(line)
                if is_line_item:
                    output_row = '"{}","{}","Takeout","{}","${}","Mike"'.format(
                        clean_text(restaurant_name),
                        clean_text(is_line_item.group(
                            1) + ' ' + is_line_item.group(2)),
                        order_date,
                        is_line_item.group(3),
                    )
                    data_rows.append(output_row)
                    print(output_row)
                    continue

                is_fee_item = FEE_ITEM_PATTERN.match(line)
                if is_fee_item:
                    output_row = '"{}","{}","Takeout","{}","${}","Mike"'.format(
                        clean_text(restaurant_name),
                        clean_text(is_fee_item.group(1)),
                        order_date,
                        is_fee_item.group(2),
                    )
                    data_rows.append(output_row)
                    print(output_row)
    return data_rows


def convert_pdfs(some_directory):
    for item in os.listdir(some_directory):
        if item.lower().endswith('.pdf'):
            check_call([PDF_TO_TEXT_PATH] + PDF_TO_TEXT_ARGS + [os.path.join(some_directory, item)])
    return


def export_csv(output_name, some_data_text_rows):
    with open(output_name, 'w', newline='') as output_handle:
        output_handle.writelines('\n'.join(some_data_text_rows))
    return


# -- CLI Hook -- #
if __name__ == '__main__':
    main()
