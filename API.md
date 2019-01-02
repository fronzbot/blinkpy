# BlinkMonitorProtocol
Unofficial documentation for the Client API of the Blink Wire-Free HD Home Monitoring &amp; Alert System.

Copied from https://github.com/MattTW/BlinkMonitorProtocol

I am not affiliated with the company in any way - this documentation is strictly **"AS-IS"**.  My goal was to uncover enough to arm and disarm the system programatically so that I can issue those commands in sync with my home alarm system arm/disarm.  Just some raw notes at this point but should be enough for creating programmatic APIs.    Lots more to be discovered and documented - feel free to contribute!

The Client API is a straightforward REST API using JSON and HTTPS.

## Login

Client login to the Blink Servers.

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "Content-Type: application/json" --data-binary '{
>  "password" : "*your blink password*",
>  "client_specifier" : "iPhone 9.2 | 2.2 | 222",
>  "email" : "*your blink login/email*"
>}' --compressed https://rest.prod.immedia-semi.com/login

**Response:**
>{"authtoken":{"authtoken":"*an auth token*","message":"auth"},"networks":{"*network id*":{"name":"*name*","onboarded":true}},"region":{"*regioncode for endpoint*":"*region name"}}

**Notes:**
The authtoken value is passed in a header in future calls.
The region code for endpoint is required to form the URL of the REST endpoint for future calls.
Depending on the region you are registered you will need to change the REST endpoints below:
- from `https://rest.prod.immedia-semi.com`
- to `https://rest.prde.immedia-semi.com` if e.g. your device is registered in Germany
Please note that at this moment it seems that all regions are not implemented equally: not all endpoints are available in all regions

## Networks

Obtain information about the Blink networks defined for the logged in user.

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/networks

**Response:**
JSON response containing information including Network ID and Account ID.

**Notes:**
Network ID is needed to issue arm/disarm calls


## Sync Modules

Obtain information about the Blink Sync Modules on the given network.

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/network/*network_id_from_networks_call*/syncmodules

**Response:**
JSON response containing information about the known state of the Sync module, most notably if it is online

**Notes:**
Probably not strictly needed but checking result can verify that the sync module is online and will respond to requests to arm/disarm, etc.


## Arm
 
Arm the given network (start recording/reporting motion events)

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --data-binary --compressed https://rest.prod.immedia-semi.com/network/*network_id_from_networks_call*/arm

**Response:**
JSON response containing information about the arm command request, including the command/request ID

**Notes:**
When this call returns, it does not mean the arm request is complete,  the client must gather the request ID from the response and poll for the status of the command.

## Disarm

Disarm the given network (stop recording/reporting motion events)

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --data-binary --compressed https://rest.prod.immedia-semi.com/network/*network_id_from_networks_call*/disarm

**Response:**
JSON response containing information about the disarm command request, including the command/request ID

**Notes:**
When this call returns, it does not mean the disarm request is complete,  the client must gather the request ID from the response and poll for the status of the command.


## Command Status

Get status info on the given command

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/network/*network_id*/command/*command_id*

**Response:**
JSON response containing state information of the given command, most notably whether it has completed and was successful.

**Notes:**
After an arm/disarm command, the client appears to poll this URL every second or so until the response indicates the command is complete.

**Known Commands:**
lv_relay, arm, disarm, thumbnail, clip

## Home Screen

Return information displayed on the home screen of the mobile client

**Request:**
>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/homescreen

**Response:**
JSON response containing information that the mobile client displays on the home page, including:  status, armed state, links to thumbnails for each camera, etc.

**Notes:**
Not necessary to as part of issuing arm/disarm commands, but contains good summary info.

## Events, thumbnails & video captures

**Request**
Get events for a given network (sync module) -- Need network ID from home 

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/events/network/*network__id*

**Response**
A json list of evets incluing URL's.   Replace the "mp4" with "jpg" extension to get the thumbnail of each clip


**Request**
Get a video clip from the events list

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed **video url from events list.mp4** > video.mp4

**Response**
The mp4 video

**Request**
Get a thumbnail from the events list

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed **video url from events list.jpg** > video_thumb.jpg

**Response**
The jpg bytes. 

**Notes**
Note that you replace the 'mp4' with a 'jpg' to get the thumbnail

**Request**
Captures a new thumbnail for a camera

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --data-binary --compressed https://rest.prod.immedia-semi.com/network/*network_id*/camera/*camera_id*/thumbnail

**Response**
Command information. 

**Request**
Captures a new video for a camera

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --data-binary --compressed https://rest.prod.immedia-semi.com/network/*network_id*/camera/*camera_id*/clip

**Response**
Command information.

## Video Information

**Request**
Get the total number of videos in the system

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/api/v2/videos/count

**Response**
JSON response containing the total video count.

**Request**
Gets a paginated set of video information

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/api/v2/videos/page/0

**Response**
JSON response containing a set of video information, including: camera name, creation time, thumbnail URI, size, length

**Request**
Gets information for a specific video by ID

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/api/v2/video/*video_id*

**Response**
JSON response containing video information

**Request**
Gets a list of unwatched videos

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/api/v2/videos/unwatched

**Response**
JSON response containing unwatched video information

**Request**
Deletes a video

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --data-binary --compressed https://rest.prod.immedia-semi.com/api/v2/video/*video_id*/delete

**Response**
Unknown - not tested

**Request**
Deletes all videos

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --data-binary --compressed https://rest.prod.immedia-semi.com/api/v2/videos/deleteall

**Response**
Unknown - not tested

## Cameras

**Request**
Gets a list of cameras

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/network/*network_id*/cameras

**Response**
JSON response containing camera information

**Request**
Gets information for one camera

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/network/*network_id*/camera/*camera_id*

**Response**
JSON response containing camera information

**Request**
Gets camera sensor information

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/network/*network_id*/camera/*camera_id*/signals

**Response**
JSON response containing camera sensor information, such as wifi strength, temperature, and battery level

**Request**
Enables motion detection for one camera

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: $auth_token" --data-binary --compressed https://rest.prod.immedia-semi.com/network/*network_id*/camera/*camera_id*/enable

**Response**
JSON response containing camera information

**Request**
Disables motion detection for one camera

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: $auth_token" --data-binary --compressed https://rest.prod.immedia-semi.com/network/*network_id*/camera/*camera_id*/disable

**Response**
JSON response containing camera information

*Note*: enabling or disabling motion detection is independent of arming or disarming the system.  No motion detection or video recording will take place unless the system is armed.


## Miscellaneous

**Request**
Gets information about devices that have connected to the blink service

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/account/clients

**Response**
JSON response containing client information, including: type, name, connection time, user ID

**Request**
Gets information about supported regions

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/regions

**Response**
JSON response containing region information

**Request**
Gets information about system health

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/health

**Response**
"all ports tested are open"

**Request**
Gets information about programs

>curl -H "Host: prod.immedia-semi.com" -H "TOKEN_AUTH: *authtoken from login*" --compressed https://rest.prod.immedia-semi.com/api/v1/networks/*network_id*/programs

**Response**
Unknown.
