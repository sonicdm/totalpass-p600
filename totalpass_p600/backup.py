import os
import zipfile
from dataclasses import dataclass


@dataclass
class Backup:
    filename: str
    data: bytes

    def save(self, output_folder: str, compress: bool = False, zip_password: str = None):
        """
        save the backup file to disk

        :param output_folder: folder to save the backup to
        :param compress: whether or not to zip the backup
        :param zip_password: password to use for the zip file
        :return:
        """
        if compress:
            filename = self.filename.split(".")[0] + ".zip"
            with zipfile.ZipFile(os.path.join(output_folder, filename), "w", zipfile.ZIP_DEFLATED) as zip_file:
                if zip_password:
                    zip_file.setpassword(bytes(zip_password, encoding="utf-8"))
                zip_file.writestr(self.filename, self.data)
        else:
            filename = self.filename
            with open(os.path.join(output_folder, filename), "wb") as f:
                f.write(self.data)
