import boto3
import glob
import os

class S3Helper():

    """
    需下載boto3
    """
    def __init__(self):
        self.access_key = S3_FILE_CONF.get("ACCESS_KEY")
        self.secret_key = S3_FILE_CONF.get("SECRET_KEY")
        self.region_name = S3_FILE_CONF.get("REGION_NAME")
        self.sql_path = 'D:/backup/database'
        # 連接s3
        self.s3 = boto3.resource(
            service_name='s3',
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )
        self.client = boto3.client(
            service_name='s3',
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def upload_file_s3(self, bucket_name):
        """
        上傳本地文件到s3
        file_name: 本地文件路徑
        bucket: S3 儲存貯體名稱
        s3_file_name: 要上傳到的s3名稱
        return: 上傳成功返回True,上傳失敗返回False
        """
    
        try:
            sql_files = glob.glob(os.path.join(self.sql_path, "*.sql"))
            zip_files = glob.glob(os.path.join(self.sql_path, "*.zip"))

            for file_name in sql_files :
                s3_file_name = os.path.basename(file_name)
                self.s3.Object(bucket_name, s3_file_name).upload_file(file_name)

            for file_name in zip_files :
                s3_file_name = os.path.basename(file_name)
                self.s3.Object(bucket_name, s3_file_name).upload_file(file_name)

        except Exception as e:
            print('出錯了：' + str(e))
            return False
        return True

if __name__ == '__main__':
    S3_FILE_CONF = {
        "ACCESS_KEY": "AWS_ACCESS_KEY",
        "SECRET_KEY": "AWS_SECRET_KEY",
        "REGION_NAME": "ap-east-1",
        "UPLOAD_BUCKET_NAME": "mysql-win",
    }
    s3 = S3Helper()
    upload = s3.upload_file_s3( S3_FILE_CONF["UPLOAD_BUCKET_NAME"] )
    print(upload)