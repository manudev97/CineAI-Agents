import os
import subprocess
import requests
import json
from datetime import datetime, timedelta
import shutil
import uuid
import tempfile

class StorachaClient:
    def __init__(self, space_did="did:key:z6MkpdA1czti9srpmB63VxmdKT3iwE1Ty75JsBNSbPfwhV36"):
        self.ready = False
        self.api_url = "https://up.storacha.network/bridge"
        self.space_did = space_did
        self.auth_headers = None
        
        # Configure executable paths
        self.w3_path = self._find_executable('w3')
        self.ipfs_car_path = self._find_executable('ipfs-car')
        
        if not self.w3_path:
            raise Exception("w3 CLI not found. Install with: npm install -g @web3-storage/w3cli")
        if not self.ipfs_car_path:
            raise Exception("ipfs-car not found. Install with: npm install -g ipfs-car")

        # Generate authentication headers
        self._generate_auth_headers()
        self.ready = True

    def _find_executable(self, name):
        """Find executable in Windows"""
        # First try with .cmd version
        path = shutil.which(f"{name}.cmd")
        if path:
            return path
        # Then try without extension
        return shutil.which(name)

    def _generate_auth_headers(self):
        """Generate authentication headers for HTTP Bridge"""
        try:
            expiration = int((datetime.now() + timedelta(hours=24)).timestamp())
            
            cmd = [
                self.w3_path,
                "bridge", "generate-tokens",
                self.space_did,
                "--can", "store/add",
                "--can", "upload/add",
                "--can", "upload/list",
                "--expiration", str(expiration)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
                check=True
            )
            
            headers = {}
            for line in result.stdout.splitlines():
                if "X-Auth-Secret header:" in line:
                    headers["X-Auth-Secret"] = line.split(":")[1].strip()
                elif "Authorization header:" in line:
                    headers["Authorization"] = line.split(":")[1].strip()
            
            if not all(key in headers for key in ["X-Auth-Secret", "Authorization"]):
                raise Exception("Invalid headers generated")
            
            self.auth_headers = headers
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error generating tokens: {e.stderr}")

    def _upload_car_to_url(self, car_file, url, headers):
        """Upload CAR file to storage URL"""
        try:
            with open(car_file, 'rb') as f:
                response = requests.put(
                    url,
                    headers=headers,
                    data=f
                )
                if response.status_code not in [200, 201]:
                    raise Exception(f"Error in PUT to storage URL: {response.text}")
        except Exception as e:
            raise Exception(f"Error uploading CAR: {str(e)}")

    def upload_text(self, text, content_title="untitled"):
        """Upload text directly to Storacha with review_[content_title].txt filename"""
        temp_file = None
        car_file = None
        
        try:
            # 1. Create temporary file with review_ prefix
            sanitized_title = "".join(c for c in content_title if c.isalnum() or c in (' ', '_')).rstrip()
            clean_title = sanitized_title.replace(' ', '_')[:50]
            # Remove duplicate words (simple approach)
            unique_words = []
            for word in clean_title.split('_'):
                if word not in unique_words:
                    unique_words.append(word)
            clean_title = '_'.join(unique_words)

            # Generate filename with UUID before extension
            filename = f"review_{clean_title}_{uuid.uuid4().hex[:8]}.txt"
            temp_file = filename  # No additional suffix needed

            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(text)
            
            # 2. Convert to CAR
            car_file = f"{temp_file}.car"
            subprocess.run(
                [self.ipfs_car_path, "pack", temp_file, "-o", car_file],
                shell=True,
                check=True
            )
            
            # 3. Get CAR CID
            result = subprocess.run(
                [self.ipfs_car_path, "hash", car_file],
                capture_output=True,
                text=True,
                shell=True,
                check=True
            )
            car_cid = result.stdout.strip()
            
            # 4. Get root content CID
            root_cid_result = subprocess.run(
                [self.ipfs_car_path, "roots", car_file],
                capture_output=True,
                text=True,
                shell=True,
                check=True
            )
            root_cid = root_cid_result.stdout.strip()
            
            # 5. Get file size
            car_size = os.path.getsize(car_file)
            
            # 6. Prepare store/add payload
            store_payload = {
                "tasks": [[
                    "store/add",
                    self.space_did,
                    {"link": {"/": car_cid}, "size": car_size}
                ]]
            }
            
            # 7. Send to Storacha Bridge for store/add
            store_response = requests.post(
                self.api_url,
                headers={
                    "X-Auth-Secret": self.auth_headers["X-Auth-Secret"],
                    "Authorization": self.auth_headers["Authorization"],
                    "Content-Type": "application/json"
                },
                json=store_payload
            )
            
            if store_response.status_code != 200:
                raise Exception(f"Error in store/add: {store_response.text}")
            
            store_result = store_response.json()[0]
            
            # 8. Check if we need to upload the file
            if store_result["p"]["out"]["ok"]["status"] == "upload":
                upload_url = store_result["p"]["out"]["ok"]["url"]
                upload_headers = {
                    "content-length": str(car_size),
                    "x-amz-checksum-sha256": store_result["p"]["out"]["ok"]["headers"]["x-amz-checksum-sha256"],
                    "content-type": "application/vnd.ipld.car"
                }
                
                # Upload CAR file
                self._upload_car_to_url(car_file, upload_url, upload_headers)
            
            # 9. Register upload in space (upload/add)
            upload_payload = {
                "tasks": [[
                    "upload/add",
                    self.space_did,
                    {
                        "root": {"/": root_cid},
                        "shards": [{"/": car_cid}]
                    }
                ]]
            }
            
            upload_response = requests.post(
                self.api_url,
                headers={
                    "X-Auth-Secret": self.auth_headers["X-Auth-Secret"],
                    "Authorization": self.auth_headers["Authorization"],
                    "Content-Type": "application/json"
                },
                json=upload_payload
            )
            
            if upload_response.status_code != 200:
                raise Exception(f"Error in upload/add: {upload_response.text}")
            
            return {
                "status": "success",
                "cid": root_cid,
                "url": f"https://{root_cid}.ipfs.w3s.link",
                "filename": filename
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
        finally:
            # Clean up temporary files
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            if car_file and os.path.exists(car_file):
                os.remove(car_file)
                
    def upload_binary(self, binary_data, content_name="unnamed_binary"):
        """Upload binary data directly to Storacha"""
        temp_file = None
        car_file = None
        
        try:
            # 1. Create temporary file for the binary data
            sanitized_name = "".join(c for c in content_name if c.isalnum() or c in (' ', '_')).rstrip()
            clean_name = sanitized_name.replace(' ', '_')[:50]
            
            # Generate filename with UUID
            filename = f"{clean_name}_{uuid.uuid4().hex[:8]}"
            temp_file = filename  # No additional suffix needed
            
            # Write binary data to temp file
            with open(temp_file, "wb") as f:
                f.write(binary_data)
            
            # 2. Convert to CAR
            car_file = f"{temp_file}.car"
            subprocess.run(
                [self.ipfs_car_path, "pack", temp_file, "-o", car_file],
                shell=True,
                check=True
            )
            
            # 3. Get CAR CID
            result = subprocess.run(
                [self.ipfs_car_path, "hash", car_file],
                capture_output=True,
                text=True,
                shell=True,
                check=True
            )
            car_cid = result.stdout.strip()
            
            # 4. Get root content CID
            root_cid_result = subprocess.run(
                [self.ipfs_car_path, "roots", car_file],
                capture_output=True,
                text=True,
                shell=True,
                check=True
            )
            root_cid = root_cid_result.stdout.strip()
            
            # 5. Get file size
            car_size = os.path.getsize(car_file)
            
            # 6. Prepare store/add payload
            store_payload = {
                "tasks": [[
                    "store/add",
                    self.space_did,
                    {"link": {"/": car_cid}, "size": car_size}
                ]]
            }
            
            # 7. Send to Storacha Bridge for store/add
            store_response = requests.post(
                self.api_url,
                headers={
                    "X-Auth-Secret": self.auth_headers["X-Auth-Secret"],
                    "Authorization": self.auth_headers["Authorization"],
                    "Content-Type": "application/json"
                },
                json=store_payload
            )
            
            if store_response.status_code != 200:
                raise Exception(f"Error in store/add: {store_response.text}")
            
            store_result = store_response.json()[0]
            
            # 8. Check if we need to upload the file
            if store_result["p"]["out"]["ok"]["status"] == "upload":
                upload_url = store_result["p"]["out"]["ok"]["url"]
                upload_headers = {
                    "content-length": str(car_size),
                    "x-amz-checksum-sha256": store_result["p"]["out"]["ok"]["headers"]["x-amz-checksum-sha256"],
                    "content-type": "application/vnd.ipld.car"
                }
                
                # Upload CAR file
                self._upload_car_to_url(car_file, upload_url, upload_headers)
            
            # 9. Register upload in space (upload/add)
            upload_payload = {
                "tasks": [[
                    "upload/add",
                    self.space_did,
                    {
                        "root": {"/": root_cid},
                        "shards": [{"/": car_cid}]
                    }
                ]]
            }
            
            upload_response = requests.post(
                self.api_url,
                headers={
                    "X-Auth-Secret": self.auth_headers["X-Auth-Secret"],
                    "Authorization": self.auth_headers["Authorization"],
                    "Content-Type": "application/json"
                },
                json=upload_payload
            )
            
            if upload_response.status_code != 200:
                raise Exception(f"Error in upload/add: {upload_response.text}")
            
            return {
                "status": "success",
                "cid": root_cid,
                "url": f"https://{root_cid}.ipfs.w3s.link",
                "filename": filename
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
        finally:
            # Clean up temporary files
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            if car_file and os.path.exists(car_file):
                os.remove(car_file)
    
    def setup(self):
        """Setup method for compatibility with earlier code"""
        return self.ready