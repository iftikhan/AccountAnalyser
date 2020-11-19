"""
This file will hold logic to clean up reporting current account status.

"""
import datetime
import logging

from botocore.exceptions import ClientError
from jinja2 import Template

from spandrel_engine.constant import Constant
from spandrel_engine.send_email import send_email

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def generate_report(findings):
    # Sign URL Expire time in sec (Total 7 days)
    expires_in = 60 * 60 * 24 * 7

    # TODO start
    Constant.SHARED_RESOURCE_BUCKET = "estestme"
    company_name = "tets"
    # TODO end

    key = f"se_report_{datetime.datetime.now()}"

    try:

        if not findings:
            raise Exception("This is no account records in database to report")
        else:
            # # XLS Flow
            # workbook = xlwt.Workbook()
            # worksheet = workbook.add_sheet('SpandrelEngineReport')
            # cols_data = [key for key, value in findings[0].items()]
            #
            # # Adding headers
            # for i, field_name in enumerate(cols_data):
            #     worksheet.write(0, i, field_name)
            #     worksheet.col(i).width = 6000
            #
            # style = xlwt.easyxf('align: wrap yes')
            # # Adding  row data
            # for row_index, row in enumerate(findings):
            #     for cell_index, cell_value in enumerate(row.items()):
            #         cell_value = cell_value[1]
            #         if isinstance(cell_value, basestring):
            #             cell_value = re.sub("\r", " ", cell_value)
            #         else:
            #             cell_value = str(cell_value)
            #             cell_value = re.sub("\r", " ", cell_value)
            #         if not cell_value:
            #             cell_value = None
            #         worksheet.write(row_index + 1, cell_index, cell_value, style)
            #
            # # uncomment below line if you want to save it in local file system
            # # workbook.save('output.xls')
            #
            # # Reading xls data to upload on s3
            # fp = io.BytesIO()
            # workbook.save(fp)
            # fp.seek(0)
            # data = fp.read()
            # fp.close()
            #
            # # Uploading xls data to upload to s3
            # s3_client = boto3.client('s3')
            # s3_client.put_object(Body=data, Bucket=Constant.SHARED_RESOURCE_BUCKET,
            #                      Key=f"{key}.xls")
            #
            # # generate pre-signed url
            # xls_link = s3_client.generate_presigned_url('get_object',
            #                                             Params={'Bucket': Constant.SHARED_RESOURCE_BUCKET,
            #                                                     'Key': f"{key}.xls"},
            #                                             ExpiresIn=expires_in)

            # HTML Flow
            # jinja2 Template
            template = Template("<table> "
                                "{% set glob={'isHeader':true} %}"
                                "{% for account in accounts %}"
                                "{% if glob.isHeader %}"
                                "{% set _ = glob.update({'isHeader':false}) %}"
                                "<tr  style='background: gray;'>"
                                "{% for key,value in account.items() %}"
                                "<th > {{ key }} </th>"
                                "{% endfor %}"
                                "</tr>"
                                "{% endif %}"
                                "<tr>"
                                "{% for key,value in account.items() %}"
                                "<td> {{ value }} </td>"
                                "{% endfor %}"
                                "</tr>"
                                "{% endfor %}"
                                "</table>"
                                "<style>"
                                "th {background-color: #4CAF50;color: white;}"
                                "th, td {padding: 5px;text-align: left;}"
                                "tr:nth-child(even) {background-color: #f2f2f2;}"
                                "</style>")

            # Generate HTML
            report_data = template.render(accounts=findings)
            # Upload HTML data to s3
            send_email(report_data)
            s3_client.put_object(Body=bytes(report_data, 'utf-8'), Bucket=Constant.SHARED_RESOURCE_BUCKET,
                                 Key=f"{key}.html")
            # generate pre-signed url
            html_link = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': Constant.SHARED_RESOURCE_BUCKET,
                                                                 'Key': f"{key}.html"},
                                                         ExpiresIn=expires_in)

            print(xls_link)
            print(html_link)

    except ClientError as ce:
        raise ce
    except Exception as ex:
        raise ex

    return {'Status': Constant.StateMachineStates.COMPLETED, 'CompanyName': company_name}
