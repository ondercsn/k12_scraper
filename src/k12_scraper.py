import os, re, requests, json, logging
from src.endpoints import *


class K12Scraper:
    settings = {}
    request = None

    def __init__(self, app, username, password, target_dir, app_id=None, h_app_id=None):

        if app not in endpoints:
            raise Exception("Uygulama mevcut degil")

        self.endpoint = endpoints[app]
        self.username = username
        self.password = password
        self.target_dir = target_dir
        self.request = requests.Session()

        self.app_id = app_id or self.endpoint['app_id']
        self.h_app_id = h_app_id or self.endpoint['h_app_id']

        self.request.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/102.0.0.0 Safari/537.36"})

    def gen_url(self, url_text):
        try:
            return self.settings["hostUrl"] % url_text
        except:
            return global_endpoint["request_url"] % url_text

    def login(self):
        login_data = {"userName": self.username, "password": self.password, "createPersistentCookie": True}
        try:
            login_response_raw = self.request.post(
                url="%s/Authentication_JSON_AppService.axd/Login" % self.endpoint['base_url'],
                json=login_data)
            login_response = json.loads(login_response_raw.text)
            logging.info(self.username, " kullanicisi giris yapti")

        except Exception as e:
            raise Exception("Giris basarisiz veya gecersiz veri ", e)

        if login_response['d']:
            self.request.cookies.set("CurrentUserName", self.username, domain=global_endpoint['cookie_domain'],
                                     path="/")
            self.request.cookies.set("Culture", "tr", domain=global_endpoint['cookie_domain'])
            self.request.cookies.set("UICulture", "tr", domain=global_endpoint['cookie_domain'])
            self.request.headers.update({'AppID': self.app_id})
            self.request.headers.update({'HAppID': self.h_app_id})

            if self.get_settings():
                self.request.headers.update(
                    {'Referer': "%s/%s" % (self.endpoint['base_url'], self.settings['applicationPath'])})
                return True

        return False

    def get_settings(self):
        settings_result = self.request.get(self.gen_url("GWCore.Web/api/Settings/Global"))
        if settings_result.status_code == 200:
            regex = r"globalSettings\.(.*)=\"(.*)\""
            matches = re.findall(regex, settings_result.text)
            for match in matches:
                self.settings[match[0]] = match[1]

        if len(self.settings) > 0:
            return True

        return False

    def fetch_messages(self):
        result = []

        if self.login():
            try:
                self.request.post(self.gen_url("GWCore.Web/api/Login/UserInfo"), json={})
                uuid = self.request.get(self.gen_url("GWCore.Web/api/Portals")).json()[0]['ID']
                self.request.post(self.gen_url("GWCore.Web/api/Portals/SetPortal"), json=uuid)
                self.request.post(self.gen_url("GWCore.Web/api/Portals/HasMissingInfo"))
            except Exception as e:
                raise Exception("Giris sonrasi oturum olusturulamadi ", e)

            self.request.headers.update({'Referer': "%s/SPTS.Web/WebParts/Student/" % self.endpoint['base_url']})

            json_data = {
                "$where": "(it.TypeID!=Guid(\"927daafc-85de-dd11-8b60-0019d1638957\")&&it.TypeID!=Guid("
                          "\"b502ee2f-d6e1-e411-bf01-3c15c2ddcd05\")&&it.TypeID!=Guid("
                          "\"18f5a18d-31e0-e411-bf01-3c15c2ddcd05\"))",
                "$orderby": "it.SendDate desc", "$take": 25, "$includeTotalCount": "True",
                "$loadOptions": ["Sender/Name", "Type"]
            }

            messages = []
            try:
                messages = self.request.post(
                    self.gen_url("SPCore.Web/api/Messages/{883fbca4-819e-a47d-339c-f528b7bdc63b}/Inbox"),
                    json=json.dumps(json_data)).json()
            except Exception as e:
                raise Exception("Mesajlar cekilemedi ", e)

            for message in messages:
                try:
                    mid = message['ID']
                    result.append(mid)
                except Exception:
                    pass
        else:
            raise Exception("Hatali kullanici bilgisi")

        return result

    def fetch_attachments(self, messages):
        result = []
        if len(messages) > 0:
            self.request.headers.update({"Content-Type": "application/json;charset=UTF-8"})
            try:
                attachment_request = self.request.post(
                    "%s/SPCore.Web/api/Messages/Attachments" % self.endpoint['base_url'],
                    data=json.dumps(messages))
            except Exception as e:
                raise Exception("Mesaj ekleri alinamadi ", e)

            if attachment_request.status_code == 200:
                attachment_datas = json.loads(attachment_request.text)

                for attachment_data in attachment_datas:
                    file_name = attachment_data['FileName']
                    img_id = attachment_data['ID']
                    extension = file_name.split(".")[1]
                    insert_date = attachment_data['InsertDate']

                    url_path_ext = "GetFile"
                    if extension.lower() in ['jpeg', 'jpg', 'png', 'tiff']:
                        url_path_ext = "GetImage"

                    target_file_name = "%s.%s" % (img_id, extension)
                    file_url = "%s/%s.aspx?path=Attachments/%s" % (
                        self.settings['pictureServerUrl'], url_path_ext, target_file_name)

                    result.append({'source': file_url, 'target': target_file_name, 'date': insert_date})
            else:
                print("Mesaj eki yok")

        return result

    def download_file(self, args):
        source_url = args['source']
        target_file = "%s/%s__%s" % (self.target_dir, re.sub('[^a-zA-Z0-9 \n\.]', '-', args['date']), args['target'])

        file_header = self.request.head(source_url)
        remote_file_size = int(file_header.headers['Content-Length'])

        if source_url and target_file:
            print(args['target'])
            if not os.path.exists(target_file) or remote_file_size != os.path.getsize(target_file):
                print("Indiriliyor...")
                with open(target_file, "wb") as f:
                    imgdata = self.request.get(source_url, stream=True)
                    f.write(imgdata.content)
