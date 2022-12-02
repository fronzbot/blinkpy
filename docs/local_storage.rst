=========================
Sync Module Local Storage
=========================

Description of how I think the local storage API is used by Blink
--------------

Since local storage is within a customer's residence, there are no guarantees for latency
and availability.  As a result, the API seems to be built to deal with these conditions.

In general, the approach appears to be this:  The Blink app has to query the sync
module for all information regarding the stored clips.  On a click to view a clip, the app asks
for the full list of stored clips, finds the clip in question, uploads the clip to the
cloud, and then downloads the clip back from a cloud URL. Each interaction requires polling for
the response since networking conditions are uncertain.  The app also caches recent clips and the manifest.

API steps
--------------
1. Request the local storage manifest be created by the sync module.

   * POST **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/request**
   * Returns an ID that is used to get the manifest.

2. Retrieve the local storage manifest.

   * GET **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/request/{manifest_request_id}**
   * Returns full manifest.
   * Extract the manifest ID from the response.

3. Find a clip ID in the clips list from the manifest to retrieve, and request an upload.

   * POST **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/{manifest_id}/clip/request/{clip_id}**
   * When the response is returned, the upload has finished.

4. Download the clip using the same clip ID.

   * GET **{base_url}/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/manifest/{manifest_id}/clip/request/{clip_id}**