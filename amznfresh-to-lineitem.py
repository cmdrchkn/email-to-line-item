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
DATE_PATTERN = re.compile(
    r'\s*Shipped\s+on\s+((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).+)'
)
# LINE_ITEM_PATTERN = re.compile(r'^\s*(\S.+)\$(\d+\.\d+)$')
LINE_ITEM_PATTERN = re.compile(r'^\s*(\d) of: (\S.+)\$(\d+\.\d+)$')
FEE_ITEM_PATTERN = re.compile(
    r'.*(Shipping & Handling|Bottle Deposit Fee|Estimated tax to be collected|Tip \(optional\)):?\s+\$?(\d+\.\d{2})'
)


# -- Main -- #
def main():
    source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        if source_dir.endswith('\\') or source_dir.endswith('/'):
            source_dir = source_dir[0:-1]

        print('-- Converting PDFs in "{}" to Text'.format(source_dir))
        convert_pdfs(source_dir)
        all_data_rows = []
        for thing in os.listdir(source_dir):
            if thing.lower().endswith('.txt'):
                print('-- Parsing text for "{}"'.format(thing))
                all_data_rows.extend(parse_text(
                    os.path.join(source_dir, thing)))

        if all_data_rows:
            output_csv = source_dir + '-amzn.csv'
            print('-- Exporting to CSV "{}"'.format(output_csv))
            export_csv(
                output_csv,
                ['"Restaurant","Item","Category","Order Date","Price","Purchased By"'] + all_data_rows
            )


def clean_text(some_string):
    if not some_string:
        return ''
    some_string = re.sub(DISALLOWED_CHARS_PATTERN, ' ', some_string.strip())
    some_string = re.sub(EXTRA_WHITESPACE_PATTERN, ' ', some_string.strip())
    return some_string


def parse_text(some_text_path):
    debug = True
    data_rows = []
    with open(some_text_path, 'r') as txtfile:
        restaurant_name = 'Amazon Fresh'
        order_date = None

        fee_item_section = False
        line_item_section = False

        for line in txtfile.readlines():
            output_row = ''

            if not order_date:
                # if debug:
                #     print('\t - Checking for Date in """{}"""'.format(line))
                is_date = DATE_PATTERN.match(line)
                if is_date:
                    order_date = clean_text(is_date.group(1))
                    if debug:
                        print('\t- Found Date {}'.format(order_date))
                    line_item_section = True
                    continue

            if '$' in line:
                if line_item_section:
                    is_line_item = LINE_ITEM_PATTERN.match(line)
                    #(quantity)(item name)(price)
                    if is_line_item:
                        output_row = '"{}","{} of: {}","Groceries","{}","${}","Mike"'.format(
                            clean_text(restaurant_name),
                            clean_text(is_line_item.group(1)),
                            clean_text(is_line_item.group(2)),
                            order_date,
                            float(is_line_item.group(3)) * int(is_line_item.group(1)),
                        )
                        data_rows.append(output_row)
                        if debug:
                            print('\t' + output_row)
                        continue
                
            if fee_item_section:
                is_fee_item = FEE_ITEM_PATTERN.match(line)
                # if 'Tip' in clean_text(line):
                #     print(line)
                if is_fee_item:
                    output_row = '"{}","{}","Groceries","{}","${}","Mike"'.format(
                        clean_text(restaurant_name),
                        clean_text(is_fee_item.group(1)),
                        order_date,
                        is_fee_item.group(2),
                    )
                    data_rows.append(output_row)
                    if debug:
                        print('\t' + output_row)
                # elif debug:
                #     print('\t- Not a fee: """{}"""'.format(line))
            
            if 'Shipping Address' in line:
                fee_item_section = True
                line_item_section = False
    return data_rows


def convert_pdfs(some_directory):
    for item in os.listdir(some_directory):
        if item.lower().endswith('.pdf'):
            check_call([PDF_TO_TEXT_PATH] + PDF_TO_TEXT_ARGS +
                       [os.path.join(some_directory, item)])


def export_csv(output_name, some_data_text_rows):
    with open(output_name, 'w', newline='') as output_handle:
        output_handle.writelines('\n'.join(some_data_text_rows))


# -- CLI Hook -- #
if __name__ == '__main__':
    main()
