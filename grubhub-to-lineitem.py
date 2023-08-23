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
    r'\s*(Your (delivery |pickup )?order from (.+?) +is +being|\s*Thanks for your (.+?) order)'
)
DATE_PATTERN = re.compile(
    # r'Grubhub\s+<orders@eat.grubhub.com>\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).+?)\s+at\s+\d'
    # r'^(\s*Date:\s+|\s+Ordered:\s+)(\d{1,2}\/\d{1,2}\/202\d|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).+?),'
    r'^(\s+Ordered:\s+)((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})'
)
LINE_ITEM_PATTERN = re.compile(r'\s*(\d)\s+([A-Za-z0-9 &\-*."\'#,()]+)\s+\$(\d+\.\d+)$')
FEE_ITEM_PATTERN = re.compile(
    r'(Delivery +fee|Sales +tax|Service +fee|Tip)\s+\$(\d+\.\d+)$'
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
            output_csv = source_dir + '-gh.csv'
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
        restaurant_name = None
        order_date = None
        for line in txtfile.readlines():
            # print('checking >' + line)
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
                    print('\t found date >{}< in line >>{}<<'.format(is_date.group(2), line))
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
                    if debug:
                        print('\t' + output_row)
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
                    if debug:
                        print('\t' + output_row)
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
