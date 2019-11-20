import argparse
import csv
import logging
import os
import sys

import time
from selenium import webdriver

reload(sys)
sys.setdefaultencoding('utf8')
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(root_dir)

logging.basicConfig(format='[%(asctime)s > %(module)s:%(lineno)d %(levelname)s]:%(message)s', level=logging.INFO,
                    datefmt='%d/%m/%y %I:%M:%S')

on_screen_logger = logging.getLogger()


class SpyFuCrawl(object):
    base_url = 'https://www.spyfu.com/overview/domain?query={}'
    driver = None

    def __init__(self, in_args):
        self.logger = on_screen_logger
        self.input_csv = in_args.input_csv
        self.start_serial = in_args.start
        self.end_serial = in_args.end

    def run(self):

        out_csv = self.input_csv.replace(".csv", "__out_{}_{}.csv".format(self.start_serial, self.end_serial))

        input_csv_data = []
        with open(self.input_csv, 'rb') as in_csv:
            csv_reader = csv.DictReader(in_csv)
            for row in csv_reader:
                input_csv_data.append(row)
            out_headers = csv_reader.fieldnames + ['seo_clicks', 'ad_spend', 'error']

        if self.start_serial and self.end_serial:
            input_csv_data = filter(lambda x: self.start_serial <= int(x['serial']) <= self.end_serial, input_csv_data)

        self.start_scrape(input_csv_data, out_csv, out_headers)

    def start_scrape(self, input_data, output_csv, out_headers):

        self.driver = webdriver.Chrome()

        with open(output_csv, "w") as _wf:
            out_writer = csv.DictWriter(_wf, fieldnames=out_headers, lineterminator="\n")
            out_writer.writeheader()
            for row in input_data:
                try:
                    f_row = row
                    try:
                        domain_data = self.get_domain_info(row.get('domain'))
                        f_row['seo_clicks'] = data_filter.str2number(domain_data.get('seo_clicks'), force_int=True)
                        f_row['ad_spend'] = data_filter.str2number(domain_data.get('ad_spend'))
                        f_row['error'] = domain_data.get('error')
                    except Exception as e:
                        error = "{} at {}".format(e, sys.exc_info()[2].tb_lineno)
                        f_row['error'] = error
                    finally:
                        self.logger.info("Writing row into CSV: {}".format(f_row))
                        out_writer.writerow(f_row)
                except Exception as e:
                    self.logger.error("Error while writing info for domain [e]: {}".format(domain_data, e))

    def get_domain_info(self, domain):

        seo_clicks_text = None
        adwords_budget_text = None
        error = None

        if self.driver:
            try:
                formatted_url = self.base_url.format(domain)
                self.logger.info("Scraping information from: {}".format(formatted_url))
                self.driver.get(formatted_url)
                time.sleep(5)
                try:
                    seo_info_card = self.driver.find_elements_by_css_selector('a[class="sf-panel-section first-row-right"]')
                    if seo_info_card:
                        seo_clicks_card = seo_info_card[0]
                        if seo_clicks_card:
                            seo_clicks = seo_clicks_card.find_elements_by_css_selector('span')
                            if seo_clicks:
                                seo_clicks_text = seo_clicks[0].text
                except Exception as e:
                    self.logger.error("Error while getting seo clicks for {}: {}".format(domain, e))
                    error = "{} at {}".format(e, sys.exc_info()[2].tb_lineno)

                try:
                    ppc_info_card = self.driver.find_elements_by_css_selector('a[class="sf-panel-section second-row section-d"]')
                    if ppc_info_card:
                        adwords_info_card = ppc_info_card[1]
                        if adwords_info_card:
                            adwords_budget = adwords_info_card.find_elements_by_css_selector('span[class="sf-metricized-number"]')
                            if adwords_budget:
                                adwords_budget_text = adwords_budget[0].text
                except Exception as e:
                    self.logger.error("Error while getting AdSpend value for {}: {}".format(domain, e))
                    error = "{} at {}".format(e, sys.exc_info()[2].tb_lineno)
            except Exception as e:
                self.logger.error("Error while getting spyfu information for [{}]: {}".format(domain, e))
                error = "{} at {}".format(e, sys.exc_info()[2].tb_lineno)

        else:
            self.logger.critical("No webdriver for scraping.")

        return {"seo_clicks": seo_clicks_text, "ad_spend": adwords_budget_text, "error": error}


def parse_args():
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython ' + sys.argv[0] + " -i /path/to/input_csv")
    parser.add_argument('-i', '--input_csv', help='Input CSV in which domains are present.', required=True)
    parser.add_argument('-s', '--start', help='Starting serial.', type=int)
    parser.add_argument('-e', '--end', help='Ending serial.', type=int)

    validate_args(parser.parse_args())
    return parser.parse_args()


def validate_args(in_args):

    if not os.path.isfile(in_args.input_csv):
        raise Exception("Input file [{}] does not exist.".format(in_args.input_csv))


def main():
    args = parse_args()

    ca_enr = SpyFuCrawl(in_args=args)
    ca_enr.run()


if __name__ == '__main__':
    main()