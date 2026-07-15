# Another MVG

1. [Installation](#1-installation)  
    1.1. [HACS installation (recommended)](#option-1-hacs-installation-recommended)  
    1.2. [Manual Installation](#option-2-manual-installation)  

2. [Create a sensor for your stop / station](#2-create-a-sensor-for-your-stop--station)  

3. [Adding a card to your dashboard](#3-adding-a-card-to-your-dashboard)  
    3.1. [Add the map to your dashboard](#31-add-the-map-to-your-dashboard)

4. [Sensor configuration options](#4-sensor-configuration-options)

5. [Screenshots](#5-screenshots)  

6. [Change log](#6-change-log)  
    6.1. [How to Update / Change from Manual Installation to HACS](#61-how-to-update--change-from-manual-installation-to-hacs)

8. [Credits](#7-credits)  

9. [Disclaimer / Haftungsausschluss](#8-disclaimer--haftungsausschluss)


# Quick installation - for those who are familiar with the process.
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=another_mvg&owner=Nisbo)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=another_mvg)

* go to ```Settings``` --> ```Devices and services``` --> add integration ```another mvg``` and follow the configuration flow

* create a manual card with this content:
```
type: custom:content-card-another-mvg
entity: sensor.yourSensor
```

# Why another MVG/MVV integration for Home Assistant?

Usually, I am lazy and use the add-ons and integrations that already exist. Home Assistant has plenty of them. While there are already some MVG integrations, some of them don't work or no longer function, and they may lack the features I desire. Since I had already programmed something similar in PHP for IP-Symcon, I have now implemented it in Home Assistant as well.


> [!IMPORTANT]
> **This is an inofficial integration and does NOT belong to the MVG / MVV.**
> 
> **The use of the data (API) is for private non commercial use only (due to MVG rules, see bottom of this page).**
> 
> **MVG does not guarantee the availability or maintenance of the interface being used.**
> 
> **The integration itself, can be used private and comercial.**

| Some | Screenshots |
|------|------|
| <img src="https://github.com/Nisbo/another_mvg/assets/26260572/c679ee24-23a4-4ed5-8c15-858794d51f68" alt="c679ee24-23a4-4ed5-8c15-858794d51f68" width="320"/> <br /> The normal View in a dashboard | <img src="https://github.com/Nisbo/another_mvg/assets/26260572/4a9133e4-4047-4fce-9240-0dbdbdf0e3c2" alt="20240301_152359025_iOS" width="500"/> <br /> On an Alexa Show 15 with [MyPage](https://www.amazon.de/XdreaM-MyPage/dp/B09CG879RG) addon |
| <img src="https://github.com/user-attachments/assets/59798b08-e622-4466-8229-1711bdd73221" alt="59798b08-e622-4466-8229-1711bdd73221" width="400"/> <br /> On an old Fire Tablet with [Wallpanel](https://wallpanel.xyz/) | <img src="https://github.com/user-attachments/assets/ed7e95b9-5dcb-492e-a110-b9cd90e22c6b" alt="ed7e95b9-5dcb-492e-a110-b9cd90e22c6b" width="200"/> <br /> On a [WT32-SC01 Plus](https://www.antratek.de/wt32-sco1-plus) with [OpenHASP](https://www.openhasp.com) Needs additional coding in automations.|

More [Screenshots](#5-screenshots) at the bottom of this document.

# 1. Installation
## Option 1: HACS installation (recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=another_mvg&owner=Nisbo)

Or use these steps:
* In Home Assistant go to the HACS integration (you can find the link in the left admin menu)
* on the top right click on the 3 dots
* click on "Custom Repositories"
* Repository: https://github.com/Nisbo/another_mvg
* Category: Integration
* click on add (bottom right)
* close the configuration popup (X on the top right)
* search for "Another MVG" and click on it
* click on download (bottom right)
* Restart HA


## Option 2: Manual Installation
* Copy the [another_mvg](https://github.com/Nisbo/another_mvg/tree/main/custom_components) folder (the folder, not only the content of the folder) from the ```custom_components/``` folder to your ```config/custom_components/``` folder.
* Restart HA

# 2. Create a sensor for your stop / station
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=another_mvg)

Or use these steps:
* go to ```Settings``` (```Einstellungen```)
* go to ```Devices and services``` (```Geräte und Dienste```)
* click on ```+ ADD INTEGRATION``` (```INTEGRATION HINZUFÜGEN```)
* search for ```another mvg``` and follow the configuration flow

1. Search for your stop / station

2. Select the correct stop from the matches and configure the wanted settings.

3. There are a lot of options but normally there is no need to configure all of them. The easiest way is to select the Global ID and click on ```SUBMIT``` (```BESTÄTIGEN```).

| German | English |
|------|------|
| ![grafik](https://github.com/user-attachments/assets/6e45440b-4a4e-478c-80f5-fd8799a8e018) | ![grafik](https://github.com/user-attachments/assets/91910f38-1d63-4850-b482-87a4346b2057) |
| ![grafik](https://github.com/user-attachments/assets/bde44c38-aea8-4be6-941b-41ee9483854d) | ![grafik](https://github.com/user-attachments/assets/aeefdba7-e4a9-4478-ad2c-6c11818abe67) |
| Filter für Linien und Ziele | Filter for lines and destinations |
| ![grafik](https://github.com/user-attachments/assets/996042c3-a337-4c9d-8b3e-7ecc68e10735) | ![grafik](https://github.com/user-attachments/assets/4146f6c0-b68a-4a0d-9bd3-3200932d0f0c) |
| Erweiterte Einstellungen | Advanced options  |
| ![grafik](https://github.com/user-attachments/assets/bab782bf-e68a-445f-8a90-7c4877a659c8) | ![grafik](https://github.com/user-attachments/assets/aaa530fc-2043-49d9-be2d-ff24585e6c06) |


⚠️ It may take a minute to create the entity

# 3. Adding a card to your dashboard
* create a manual card with this content:
```
type: custom:content-card-another-mvg
entity: sensor.yourSensor
```
* create a manual card with this content, if you want to use the card with the big font as a single card:
```
type: custom:content-card-another-mvg-big
entity: sensor.yourSensor
```
* replace ```sensor.yourSensor``` with the entity ID of your Another MVG sensor.
* Enjoy

⚠️ If you get the error that ```custom:content-card-another-mvg``` doesnt exist, clear the frontend / browser cache.





### 3.1 Add the map to your dashboard

![grafik](https://github.com/user-attachments/assets/138f06bc-dc74-4dc6-b0ee-fbdc49af74e7)

The card can be added and configured directly through the map selector, like other cards. 
Simply go to your dashboard, click on "Add Card", search for "Another MVG", and select the card from the results.

![grafik](https://github.com/user-attachments/assets/aac03dfb-9358-4787-a1f8-0923aeb1db1a)

![grafik](https://github.com/user-attachments/assets/da13be9f-e8cf-461d-a907-7841b89bbc8a)

That’s all. In the standard configuration, it shows the complete map. 
If you want to zoom in, follow the instructions in the description. 
This editor is currently only available in German because I have no clue how to add language support to the card. 
If there is a real need, I can create an additional card for English users.

If, for some reason, you are not able to find the card, try clearing your frontend and browser cache, or try configuring the card on your own.

```
type: custom:content-card-another-mvg-livemap
mode: schematic
x: "2750800"
y: "1560005"
zoom: "4.8"
``` 


# 4. Sensor configuration options

Another MVG is configured through the Home Assistant UI. YAML based sensor configuration is deprecated and should no longer be used for new setups.

Existing YAML sensors from older versions are migrated to GUI entries automatically. After the migrated sensors are visible in Home Assistant under `Settings` --> `Devices & services` --> `Another MVG`, the old YAML configuration can be removed from your Home Assistant configuration.

## Basic fields

### Station / Global ID

The station identifier is the technical ID of a stop, station or location. Another MVG uses this identifier instead of the station name because it is clearer for the API and avoids ambiguous station names.

Usually you do not have to search this ID manually. Use the integration setup flow, enter the station name, and select the correct stop from the search result.

If you want to look up a Global ID manually, you can use the MVG location endpoint in a browser and replace the query text:

`https://www.mvg.de/api/bgw-pt/v3/locations?query=pasing`

https://www.mvg.de/api/bgw-pt/v3/locations?query=pasing

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/ec7bfb9b-48a0-45bc-a50d-16d960433caa)

### Name

This is the display name used for the sensor and as the default card title. It is not used for the API request itself.

### Monitor type

Choose what this sensor should provide:

* `Departure monitor` uses the MVG departure API and shows departures from the selected stop.
* `Arrival monitor` uses the MVV/EFA arrival API and shows arrivals at the selected stop.

For compatibility, older sensors default to `Departure monitor`.

## Transport types and request limit

### Transport types

Select the transport types that should be requested by the sensor.

Available values include:

* `SBAHN`
* `UBAHN`
* `TRAM`
* `BUS`
* `REGIONAL_BUS`
* `BAHN`

`BUS` and `REGIONAL_BUS` are different API values. In practice, some lines may appear in one or the other, so selecting both is often useful when you want to see all bus traffic.

`BAHN` can be used for regular trains. This is available, but not as deeply styled and integrated as the common MVG/MVV transport types.

For arrival monitors, transport types are used as a prefilter in the MVV/EFA API request. This can reduce the response size and avoids loading transport types you do not need.

### Request limit

The request limit defines how many entries the API should request. The default is `40`; the integration limits the value internally to `80`.

The sensor-level limit is a data request limit, not a guaranteed number of visible rows in the card. If you use sensor prefilters for lines or directions, fewer entries may remain after filtering.

For busy stations such as Pasing or Hauptbahnhof, a higher value gives card filters more data to work with. For smaller stops, the default is usually enough.

## Sensor prefilters: lines and directions

These filters are applied inside the sensor. That means filtered-out entries are not stored in the Home Assistant sensor attributes and cannot be shown by any card later.

For different dashboard views, prefer the filter options in the card editor. Use sensor prefilters when you intentionally want to reduce the amount of stored data or API result data.

### Only these lines

Shows only entries for specific lines, for example `S3,S4,S20` or `860,831,843`.

Multiple lines can be separated by comma or semicolon.

### Hide this direction / origin

For departure monitors this hides destinations. For arrival monitors this hides origins.

Use the exact text as it appears in the card. Multiple values should be separated by semicolon:

`Graßlfing, Olchinger See;Olching, Georgenstraße`

Semicolon is recommended because commas may be part of station or direction names.

### Only this direction / origin

For departure monitors this keeps only matching destinations. For arrival monitors this keeps only matching origins.

Use semicolon-separated values when entering more than one direction or origin.

## Advanced settings

### Additional station / Global ID 2

You can combine a second station into the same sensor. This can be useful when two stops are close together, for example a train station and a bus stop.

Keep in mind that the integration needs to perform an additional API request for the second station. If you use this on many sensors, the risk of blocked or delayed API requests increases.

### Increased limit

This option can help when many filters are used and entries after midnight are missing. Increase it carefully, preferably in small steps, because it can create additional API requests.

### Time zone options

Default is `Europe/Berlin`. Normally this should not be changed.

If your system runs in UTC or you want to display times in another timezone, you can configure the source and target timezone in the advanced settings. Use timezone names such as `UTC` or `Europe/Berlin`.

### Alert attributes

You can configure lines for which additional delay attributes should be created.

Example lines: `S3,S4,S20`

For each configured line, the sensor creates attributes for the next matching connections, for example:

```
notifyLateMvgConnectionS4_1
notifyLateMvgConnectionS4_2
notifyLateMvgConnectionS4_3
```

Possible values:

* `-1` means the departure is cancelled
* `0` means the departure is on time
* values greater than `0` are the delay in minutes

These attributes can be used in Home Assistant automations as conditions.

### Status template

The status template controls the main state text of the sensor.

Available placeholders include:

* `{planned_departure}`
* `{expected_departure}`
* `{track}`
* `{transport_type}`
* `{label}`
* `{destination}`
* `{delay}`
* `{trainType}`
* `{cancelled}`
* `{plannedDepartureTime}`
* `{realtimeDepartureTime}`
* `{realtime_departure_diff_minutes}`
* `{minutes_difference}`
* `{announcement}`
* `{announcementEN}`

### Custom CSS

Custom CSS in the sensor settings applies to all Another MVG cards that use this sensor. Use this when you want the same CSS for every card showing this sensor.

The card editor also has a card-specific CSS field. Do not use both for the same styling unless you intentionally want to layer them.

### Proxy settings

The optional PHP proxy can be used as a fallback when direct API requests fail from your Home Assistant instance.

Normally this should stay disabled. Use it only if you know you need it.

### MQTT

MQTT publishing is optional and uses the MQTT integration configured in Home Assistant. You do not configure broker host, port or credentials in Another MVG.

Per sensor you can configure:

* Enable MQTT publishing
* MQTT topic prefix
* MQTT QoS
* MQTT retain

The default topic prefix is `another_mvg`. The final topic also includes the sanitized sensor entity name, for example:

`another_mvg/olching_ankunfte/state`

The payload includes the sensor name, entity ID, unique ID, monitor type, state, data freshness information and the current entries.

If `retain` is enabled, the broker keeps the last message until it is overwritten or manually cleared. Disabling MQTT in Another MVG does not automatically delete retained messages from your broker.

## Card filters vs sensor filters

The sensor configuration decides which data is requested and stored in Home Assistant.

The card configuration decides which of the available sensor entries are shown in a specific dashboard card.

If you want one dashboard card to show only S-Bahn and another card to show only buses, it is usually better to request both transport types in the sensor and then filter in the card.

If you never need certain lines, directions or transport types anywhere, use the sensor prefilters to reduce stored data.

# 5. Screenshots
## Browser View

### Pasing all departures

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/c679ee24-23a4-4ed5-8c15-858794d51f68)

Example setup: create a departure monitor for `Pasing`, keep all relevant transport types enabled, and set a request limit high enough for the number of entries you want to show.


### Pasing S3, S4, S20 western direction

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/6336adc3-8084-40bf-b4bb-2747fa13e6c1)

Example setup: create a departure monitor for `Pasing`, select `SBAHN`, filter to lines `S3`, `S4` and `S20`, and hide the directions that should not be shown.

### Bus / Regional Bus Olching - some directions and lines

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/0bfc9858-54ea-4b1a-8cd0-a031df044b1d)

Example setup: create a departure monitor for `Olching`, select `BUS` and `REGIONAL_BUS`, filter to the wanted bus lines, and hide directions that should not be shown.


### U-Bahn

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/b725a2d4-938e-479d-89d9-0bdbb714360e)

Example setup: create a departure monitor for the U-Bahn station and select `UBAHN` as transport type. The card title can be hidden in the card editor if you want a more compact display.


### Eichenau S-Bahn

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/0cd07461-b429-417e-907a-4316656dea59)

Example setup: create a departure monitor for `Eichenau`, select `SBAHN`, and use the direction filter to hide directions that should not be shown.


### Eichenau / Olching S-Bahn station combined in one card

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/c715acb4-1102-48c7-8763-77c8357a18ed)

Example setup: create one monitor for `Olching` and use `Additional station / Global ID 2` for `Eichenau`. Select `SBAHN` and configure direction filters as needed.


## Mobile App View

| Mobile App View  | Mobile App View |
| ------------- | ------------- |
| ![IMG_5431](https://github.com/Nisbo/another_mvg/assets/26260572/6c7b5d15-8d45-44f6-bc47-ff6eb4e3fde2) | ![IMG_5432](https://github.com/Nisbo/another_mvg/assets/26260572/ab42f3a4-2432-43c1-939a-2a237e39c36f) |
| ![IMG_5433](https://github.com/Nisbo/another_mvg/assets/26260572/fb3b9fd0-7753-43c8-a8e8-902e53114623) | ![IMG_5434](https://github.com/Nisbo/another_mvg/assets/26260572/0ae7381b-a0d0-4995-b241-7ca9c7b3557c) |


# 6. Change log
## 13.01.2024 - Version 1.1.0
- better error handling for connection problems

## 29.01.2024 - Version 1.2.0
- added timezone options, default is "Europe/Berlin". If your system is running with UTC settings, you can use UTC as source timezone. If you want to display a different timezone, you can define a target timezone.
- minor fixes

## 01.03.2024 - Version 1.3.0
- added an option ```alert_for: "S3,S4,S20"``` to set attributes for your sensor if the next 3 departures of defined lines are late or cancelled .... or in time. (Ref to "Alert Settings")
- there is a 2nd lovalace card for single card use. Means with big font so that you can put it on a screen or on an Amazon Show 15 (with the silk browser and the kiosk mode HA addon via Media Function from HA)
- ![20240301_152359025_iOS](https://github.com/Nisbo/another_mvg/assets/26260572/4a9133e4-4047-4fce-9240-0dbdbdf0e3c2)
- You have to add the resource ```/local/content-card-another-mvg-big.js``` as **JavaScripts-Modul** 
- improved error handling, additionally there will be an indicator on the card (Stop Name - nicht aktuell) if the data is outdated (older than 1 minute)
- fixed a bug where the sensor was updated with wrong data (thx to @msp1974 )

## 28.05.2024 - Version 1.4.0
- improved error handling
- improved error reporting in the system log
- workaround for missing track 2a (not provided by the API) in Ebersberg. It assumes that if there is no platform provided by the API that the departure is from track 2a (Gleis 2a).
- fixed an issue with CSS on some installations (possible problems with other addons)
- You can also use ```BAHN``` but this feature is not fully integrated and not enabled by default. There is also no special design / labeling available.
If you want to include it, add `BAHN` to the transport types in the sensor configuration.

## 13.08.2024 - Version 1.5.0
- Now with the option to install Another MVG via HACS
- Custom cards will be registered automatically, not longer needed to add them manually

## 16.10.2024 - Version 1.5.1
- Updated the API address

## 22.10.2024 - Version 2.0.0 (current version)
* Formerly planned and announced as v1.6.0, now released as v2.0.0 due to the **amount** of changes.
* v2.0.0 includes a complete GUI configuration, following the integration in HACS from the last version.
* Added language files for English and German.
* added "Only some destinations". Multiple values should be separated by semicolon because commas and spaces may be part of station or direction names.
* Improved error handling in the custom card if a sensor is unavailable or deleted.
  * ![grafik](https://github.com/user-attachments/assets/7735b742-8d59-4397-a65c-9b78657763be)
* Improved data handling of the custom card during startup.
  * ![grafik](https://github.com/user-attachments/assets/deb45a8b-7d5c-48f6-8d1f-b7b09731a8f4)
* Fixed the deprecation warning.
* Updated documentation to improve the installation process.


# 6.1 How to Update / Change from Manual Installation to HACS
## Update via HACS:
- After you got the update notification from Home Assistant, just click on "Install"
- restart Home Assistant
- make sure the frontend cache is cleared

## Manual Update:
- Replace all files with the new files (like during the installation) and restart HA.
- Afterwards you have to clear the frontend cache on all devices.

## Change from manual installation to HACS installation

### ⚠️ change from before v1.5.0 (< v1.5.0)
:red_circle: Due to the fact, that Custom cards will be registered (since v1.5.0) automatically, you have to remove these 2 files from your www folder. :red_circle:

```
content-card-another-mvg-big.js
content-card-another-mvg.js
```
You also have to remove these 2 cards from
Settings --> Dashboards --> 3 dots on the top right --> Resources
```
/local/content-card-another-mvg.js
/local/content-card-another-mvg-big.js
```
- Remove the old Files and follow the instructions from the HACS installation part.

### from v1.5.0 (>= v1.5.0)
- Remove the old files.
- Restart HACS
- follow the instructions from the HACS installation part.


# 7. Credits
* To all the guys in the Home Assistant forum for the help. 
* @msp1974 for his code for the card integration
* To the MVG for the API. 
* To other guys on github, were I was able to learn more about python code and Home Assistant. 
* And to my best friend Google. ^^

# 8. Disclaimer / Haftungsausschluss

### Deutsch

Die Nutzung der Home Assistant Integration **another_mvg** erfolgt auf eigene Gefahr. Der Entwickler übernimmt keine Verantwortung oder Haftung für etwaige Schäden, die durch die Verwendung dieser Integration entstehen können. Dieser Haftungsausschluss erstreckt sich auf direkte oder indirekte Schäden, finanzielle Verluste, Datenverluste, Beeinträchtigung des Systembetriebs oder andere potenzielle Unannehmlichkeiten.

Die Integration wird "wie sie ist" und ohne jegliche Gewährleistung bereitgestellt. Der Entwickler übernimmt keine Garantie für die Richtigkeit, Vollständigkeit oder Zuverlässigkeit der Funktionen dieser Integration. Es wird empfohlen, regelmäßige Sicherungen durchzuführen und alle notwendigen Sicherheitsvorkehrungen zu treffen, um unerwünschte Folgen zu vermeiden.

Die Benutzer sind angehalten, die Anweisungen und Empfehlungen in der Dokumentation der Integration zu befolgen. Jegliche Modifikationen oder Anpassungen an der Integration erfolgen auf eigenes Risiko und können die Funktionalität beeinträchtigen.

Durch die Verwendung dieser Home Assistant Integration erklärt sich der Benutzer mit den Bedingungen dieses Haftungsausschlusses einverstanden. Es wird empfohlen, regelmäßig auf Aktualisierungen oder Änderungen der Integration zu achten und diese entsprechend zu berücksichtigen.

### English

The use of the Home Assistant Integration **another_mvg** is at your own risk. The developer assumes no responsibility or liability for any damages that may arise from the use of this integration. This disclaimer extends to direct or indirect damages, financial losses, data loss, impairment of system operation, or other potential inconveniences.

The integration is provided "as-is" and without any warranty. The developer makes no guarantees regarding the accuracy, completeness, or reliability of the functions of this integration. It is recommended to perform regular backups and take all necessary security precautions to avoid undesirable consequences.

Users are encouraged to follow the instructions and recommendations in the documentation of the integration. Any modifications or adjustments to the integration are done at your own risk and may affect its functionality.

By using this Home Assistant Integration, the user agrees to the terms of this disclaimer. It is advised to regularly check for updates or changes to the integration and take them into consideration accordingly.


# MVG Disclaimer for the use of the data
German: ... Für private, nicht-kommerzielle Zwecke, wird eine gemäßigte Nutzung ohne unsere ausdrückliche Zustimmung geduldet. Jegliche Form von Data-Mining stellt keine gemäßigte Nutzung dar. Wir behalten uns vor, die Duldung grundsätzlich oder in Einzelfällen zu widerrufen. ...

English: ... For private, non-commercial purposes, moderate use is tolerated without our express consent. Any form of data mining does not constitute moderate use. We reserve the right to revoke our tolerance in principle or in individual cases. ...

Full (german) text can be found in the MVG impressum at the bottom.

https://www.mvg.de/impressum.html
