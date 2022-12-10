import dateutil.parser

from accountability_api.api_utils import metadata as consts
from accountability_api.api_utils import utils, query, processing
from .report import Report


class GeneratedSdsProducts(Report):
    """
    https://docs.google.com/presentation/d/1Qpk2sEkltm2rJJI-GvKiSChl2ljVQ7LDFbWURviFc7I/edit?usp=sharing

    """

    def __init__(
        self, title, start_date, end_date, timestamp, detailed=False, **kwargs
    ):
        super().__init__(
            title, start_date, end_date, timestamp, detailed=detailed, **kwargs
        )
        self._total_products_produced_num = 0
        self._total_products_volume = 0

        self._products = {}

    def populate_data(self):
        products = {}
        products = self._get_generated_products()

        self._products = products

    def _get_generated_products(self):

        indexes = {}
        indexes = consts.GENERATED_PRODUCTS

        # Go through each index in the GENERATED_PRODUCTS indexes
        products = []

        total_products_produced = 0
        total_volume = 0

        for index in indexes:
            time_key = "creation_timestamp"
            product_creation = query.construct_range_object(
                time_key,
                start_value=self.start_datetime,
                stop_value=self.end_datetime,
            )

            source_includes = [
                "metadata.FileSize",
            ]

            body = {
                "query": {"bool": {"must": [{"range": product_creation}]}},
                "_source": source_includes,
            }
            body = self.add_universal_query_params(body)

            try:
                results = query.run_query_with_scroll(
                    index=indexes[index], body=body, doc_type="_doc"
                )

                volume = processing._get_processed_volume(
                    results.get("hits", {}).get("hits", [])
                )
                num_products = len(results.get("hits", {}).get("hits", []))

                total_products_produced += num_products
                total_volume += volume

                products.append(
                    {"name": index, "files_produced": num_products, "volume": volume}
                )
            except Exception:
                print("could not find index")
                products.append({"name": index, "products_delivered": 0, "volume": 0})

        self._total_products_produced_num = total_products_produced
        self._total_products_volume = total_volume

        return products

    def get_dict_format(self):
        root_name = "GENERATED_SDS_PRODUCTS_REPORT"

        return {
            "root_name": root_name,
            "header": {
                "time_of_report": dateutil.parser.isoparse(self._creation_time).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "data_received_time_range": f"{self.start_datetime}Z - {self.end_datetime}Z",
                "crid": self._crid,
                "venue": self._venue,
                "processing_mode": self._processing_mode,
                "total_products_produced": self._total_products_produced_num,
                "total_data_volume": self._total_products_volume,
            },
            "products": self._products,
        }

    def get_data(self):
        return self._products

    def to_xml(self):
        data = self.get_dict_format()
        root_name = "root"
        if "root_name" in data:
            root_name = data["root_name"]
            del data["root_name"]

        return utils.convert_to_xml_str(root_name, data)

    def to_json(self):
        return super().to_json()

    def to_csv(self):
        return super().to_csv()

    def get_filename(self, output_format):
        return "GSP_{}_{}_{}.{}".format(
            self._report_type, self.start_datetime, self.end_datetime, output_format
        )

    def generate_report(self, output_format=None):
        return super().generate_report(output_format=output_format)
