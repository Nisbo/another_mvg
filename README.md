# another_mvg




**Why another MVG/MVV integration for Home Assistant?**

Usually, I am lazy and use the add-ons and integrations that already exist. Home Assistant has plenty of them. While there are already some MVG integrations, some of them don't work or no longer function, and they may lack the features I desire. Since I had already programmed something similar in PHP for IP-Symcon, I have now implemented it in Home Assistant as well.


This is my 1st integration for Home Assistant and also my 1st Python addon, so please be kind to me if something is not 100% perfect. ^^

> [!IMPORTANT]
> **This is an inofficial integration and does NOT belong to the MVG / MVV.**
> 
> **The use of the data (API) is for private use only (due to MVG rules, see bottom of this page).**
>
> **The integration itself, can be used private and comercial.**

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/c679ee24-23a4-4ed5-8c15-858794d51f68)

 ![20240301_152359025_iOS](https://github.com/Nisbo/another_mvg/assets/26260572/4a9133e4-4047-4fce-9240-0dbdbdf0e3c2)
 
More screenshots at the bottom of this document.

# Installation
* Copy the [another_mvg](https://github.com/Nisbo/another_mvg/tree/main/config/custom_components) folder (the folder, not only the content of the folder) from the ```config/custom_components/``` folder to your ```config/custom_components/``` folder.
* For the lovelace cards, copy the content (2 files) from the ```config/www``` folder to your ```config/www``` folder.
* Under Settings --> Dashboards --> 3 dots on the top right corner --> resourses
* Add the resource ```/local/content-card-another-mvg.js``` as **JavaScripts-Modul**
* Add the resource ```/local/content-card-another-mvg-big.js``` as **JavaScripts-Modul** (this card is for single card use only, e.g. in fullscreen kiosk mode)
* Restart HA
* Configure the configuration.yaml (see guide below)
* Check configuration.yaml with the check function under Dev-Tools
* Restart HA again
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
* replace ```sensor.yourSensor``` with the name of your sensor. Should be something with **sensor.name** where name, the name from the parameter in the configuration.yaml is.
* Enjoy


# Code for your configuration.yaml

### Add the name of this integration

To load the integration, you have to add

```  - platform: another_mvg``` **Required**

to the **sensor:** part in your configuration.

> [!CAUTION]
> Don't add the line ```sensor:``` a second time!
> If it is already there, just put ```  - platform: another_mvg``` below your other **platforms** in the sensor part.

### Define your station / stop / location
```   globalid: "de:09162:10"``` **Required**
> [!IMPORTANT]
> The station identifier of the stop/station/location. I decided to use the identifier, instead of names, because it is more clear (for the API) and leads to less problems.
The only problem you have, is to find the identifier (globalid) by your own.
Here you can find the globalid for your station.
> ```https://www.mvg.de/api/fib/v2/location?query=Pasing```
> Just replace the name in the query. If there is more than one entry, you have to find the correct one. I recommend to open the link on your PC/Notebook.

https://www.mvg.de/api/fib/v2/location?query=Pasing

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/ec7bfb9b-48a0-45bc-a50d-16d960433caa)


### Name of the display
```    name: "Pasing"``` **Required**

Is the name of the display inside the card and will be used for the sensorname. It is **NOT** the name of the station for the API call.

## Minimal configuration example
```
sensor:
  - platform: another_mvg
    name: "Pasing"
    globalid: "de:09162:10"
```
The code above, will show all connections from Pasing. (Pasing has the globalid de:09162:10)
If you want to see only Bus, Regional Bus, Tram and/or U-Bahn (U-Bahn of course not in Pasing) you have to configure the ```   transporttypes```.

## Extended Configuration

### Types of public trasportation (Bus, Regional Bus, S-Bahn ...)

```   transporttypes: "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS"```

This should be selfexplaining. Add the types of transportation **comma separated and without spaces** in between.
**BUS** and **REGIONAL_BUS** <ins>are different</ins>. **BUS** is **MVG** and **REGIONAL_BUS** is **MVV**. But it looks like, in the API they mixed it for some lines. Just <ins>add both</ins>, to be save.
As mentioned above, by default all transportations are enabled. If you want to see only some, you have to use this parameter.

You can also use ```BAHN``` but this feature is not fully integrated and not enabled by default. There is also no special design / labeling available.
If you want to include it to your departure list, you can use this code:

```   transporttypes: "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS,BAHN"```

### Show only some lines

```   onlyline: "S3,S4,S20"```

If you want to see only some lines, like S3, S4 and S20, you can configure it comma seperated.


### Hide some destinations

```   hidedestination: "Mammendorf;Maisach"```

If you want to see only some directions / destinations, you have to insert the EXACT names of the **unwanted** destinations like they are shown in the connection display. (card)
The names should be ```;``` separated. They can be ```,``` or space sepatared, but this can lead to problems if a ```,``` or a space is in the name of the destination.

```   hidedestination: "Graßlfing, Olchinger See;Olching, Georgenstraße"```

### Define the number of departures

```   limit: 15```

By default you will see 6 departures. If you want to see more or less, you have to configure it.
Please add **_only a number_ and _no quotes_**.
Die API will pull a maximum of 80 departures. 
If you use "filters" like **hidedestination**, witch filter out 40 entries, you will only see the remaining 40 as maximum.

### Hide the name of the card (the row above the yellow row)

```   hidename: True```

If you don't want to see the name of the card (the name of the station you configured in configuration.yaml with the **name** parameter) you have to set this parameter to ```True```.

### doublestationnumber

```   doublestationnumber: "2"```

> [!IMPORTANT]
> If you want to create 2 or more cards for the same globalid, you have to use this parameter. (e.g. one for BUS, one for SBAHN, one for TRAM)
It can be a number or a letter. Also more numbers or letters are possible. No special chars are allowed and also no space.

### Merge 2 different stations in one display
```   globalid2: "de:09179:6180"```

If you have 2 stations close together (or far far away) like a train station and a bus stop, you can combine both in one card.
Keep in mind, that you have to insert all transportations in ``` transporttypes```.
The use of this function can lead to problems, because there are 2 API calls in 1 second and it can happen, that the API blocks the 2nd call.
If you use it only in one card, it should be no problem. If you use more, the risk is higher that the API blocks the request.

### Time Zone options ###
Default is "Europe/Berlin".
If your system is running with UTC settings, you can use UTC in ```timezone_from```. 
If you want to display a different timezone, you can define it in ```timezone_to```
```
    timezone_from : "UTC"
    timezone_to   : "Europe/Berlin"
``` 

### Alert Settings ###

```
    alert_for: "S3,S4,S20"
``` 

If you configure this option, there will be 3 additional attributes (per line) for your sensor.
Format:
```
notifyLateMvgConnectionLine_1
notifyLateMvgConnectionLine_2
notifyLateMvgConnectionLine_3
```
If you configure the the alert for S4 the name of the attributes are as follow
```
notifyLateMvgConnectionS4_1
notifyLateMvgConnectionS4_2
notifyLateMvgConnectionS4_3
```
You can use it e.g. in an automation as condition 

```
condition:
  - condition: numeric_state
    entity_id: sensor.olching_und_eichenau
    attribute: notifyLateMvgConnectionS4_3
    above: 0
```
The possible values from ```above``` in this example are
* -1 --> departure is cancelled
* 0 --> departure is in time
* greater than 0 --> the delay in minutes of this departure

I am using this in an automation to change the color of a LED from WLED
```
alias: WLED Test - Unten Gelb
description: ""
trigger:
  - platform: state
    entity_id:
      - sensor.olching_und_eichenau
    attribute: connections
  - platform: time_pattern
    minutes: "*"
condition:
  - condition: numeric_state
    entity_id: sensor.olching_und_eichenau
    attribute: notifyLateMvgConnectionS4_3
    above: 0
action:
  - service: select.select_option
    target:
      device_id: 2e48d67fbe95d4ee7c9ef03bdf8ffe08
    data:
      option: Unten Gelb
  - service: select.select_option
    target:
      device_id: d99baaee5d4ecce453980a792ec2f3a1
    data:
      option: Bahn 3 gelb
mode: single
```
This is an example code from my WLED configuration, dont copy and paste it, if you dont know what you are doing. ;) 




## Complex configuration example
```
sensor:
  - platform: another_mvg
    name: "Olching"
    globalid: "de:09179:6110"
    hidedestination: "Mammendorf,Maisach"
    limit: 15
    transporttypes: "SBAHN"
  - platform: another_mvg
    name: "Olching Busabfahrten"
    globalid: "de:09179:6110"
    hidedestination: "Graßlfing, Olchinger See;Olching, Georgenstraße"
    onlyline: "860,831,843"
    limit: 15
    transporttypes: "BUS,REGIONAL_BUS"
    doublestationnumber: "2"
  - platform: another_mvg
    name: "Eichenau"
    globalid: "de:09179:6180"
    hidedestination: "Geltendorf,Buchenau,Grafrath"
    limit: 15
    transporttypes: "SBAHN"
  - platform: another_mvg
    name: "Eichenau Busabfahrten"
    globalid: "de:09179:6181"
    hidedestination: "Freiham (S) Süd"
    limit: 15
    transporttypes: "BUS,REGIONAL_BUS"
    onlyline: "860"
  - platform: another_mvg
    name: "Pasing"
    globalid: "de:09162:10"
    onlyline: "S3,S4,S20"
    limit: 20
    transporttypes: "SBAHN"
    hidedestination: "Deisenhofen,Holzkirchen,Grafing Bahnhof, Trudering, Ostbahnhof,Haar,Ebersberg, München Hbf, Höllriegelskreuth"
    timezone_from : "Europe/Berlin"
    timezone_to   : "Europe/Berlin"
  - platform: another_mvg
    name: "Pasing - alle Abfahrten"
    globalid: "de:09162:10"
    limit: 20
    doublestationnumber: "2"
    transporttypes: "SBAHN,BUS,REGIONAL_BUS,TRAM"
  - platform: another_mvg
    name: "Olching und Eichenau"
    globalid: "de:09179:6110"
    globalid2: "de:09179:6180"
    hidedestination: "Mammendorf,Maisach,Geltendorf,Buchenau,Grafrath"
    limit: 15
    transporttypes: "SBAHN"
    doublestationnumber: "3"
    alert_for: "S3,S4,S20"
  - platform: another_mvg
    name: "UBahn Test"
    globalid: "de:09162:360"
    transporttypes: "UBAHN"
    limit: 15
    hidename: True
```

# Browser View


### Pasing all departures

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/c679ee24-23a4-4ed5-8c15-858794d51f68)

```
  - platform: another_mvg
    name: "Pasing - alle Abfahrten"
    globalid: "de:09162:10"
    limit: 20
```


### Pasing S3, S4, S20 western direction

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/6336adc3-8084-40bf-b4bb-2747fa13e6c1)

```
  - platform: another_mvg
    name: "Pasing"
    globalid: "de:09162:10"
    onlyline: "S3,S4,S20"
    limit: 20
    transporttypes: "SBAHN"
    hidedestination: "Deisenhofen,Holzkirchen,Grafing Bahnhof, Trudering, Ostbahnhof,Haar,Ebersberg, München Hbf, Höllriegelskreuth"
```

### Bus / Regional Bus Olching - some directions and lines

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/0bfc9858-54ea-4b1a-8cd0-a031df044b1d)

```
  - platform: another_mvg
    name: "Olching Busabfahrten"
    globalid: "de:09179:6110"
    hidedestination: "Graßlfing, Olchinger See;Olching, Georgenstraße"
    onlyline: "860,831,843"
    limit: 15
    transporttypes: "BUS,REGIONAL_BUS"
```


### U-Bahn

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/b725a2d4-938e-479d-89d9-0bdbb714360e)

```
  - platform: another_mvg
    name: "UBahn Test"
    globalid: "de:09162:360"
    transporttypes: "UBAHN"
    limit: 15
    hidename: True
```


### Eichenau S-Bahn

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/0cd07461-b429-417e-907a-4316656dea59)

```
  - platform: another_mvg
    name: "Eichenau"
    globalid: "de:09179:6180"
    hidedestination: "Geltendorf,Buchenau,Grafrath"
    limit: 15
    transporttypes: "SBAHN"
```


### Eichenau / Olching S-Bahn station combined in one card

![grafik](https://github.com/Nisbo/another_mvg/assets/26260572/c715acb4-1102-48c7-8763-77c8357a18ed)

```
  - platform: another_mvg
    name: "Olching und Eichenau"
    globalid: "de:09179:6110"
    globalid2: "de:09179:6180"
    hidedestination: "Mammendorf,Maisach,Geltendorf,Buchenau,Grafrath"
    limit: 15
    transporttypes: "SBAHN"
```


# Mobile App View

| Mobile App View  | Mobile App View |
| ------------- | ------------- |
| ![IMG_5431](https://github.com/Nisbo/another_mvg/assets/26260572/6c7b5d15-8d45-44f6-bc47-ff6eb4e3fde2) | ![IMG_5432](https://github.com/Nisbo/another_mvg/assets/26260572/ab42f3a4-2432-43c1-939a-2a237e39c36f) |
| ![IMG_5433](https://github.com/Nisbo/another_mvg/assets/26260572/fb3b9fd0-7753-43c8-a8e8-902e53114623) | ![IMG_5434](https://github.com/Nisbo/another_mvg/assets/26260572/0ae7381b-a0d0-4995-b241-7ca9c7b3557c) |


# Change log
13.01.2024 - Version 1.1.0
- better error handling for connection problems

29.01.2024 - Version 1.2.0
- added timezone options, default is "Europe/Berlin" if your system is running with UTC settings, you can use UTC in ```timezone_from```. If you want to display a different timezone, you can define it in ```timezone_to```
- ```
    timezone_from : "UTC"
    timezone_to   : "Europe/Berlin"
  ``` 
- minor fixes

01.03.2024 - Version 1.3.0
- added an option ```alert_for: "S3,S4,S20"``` to set attributes for your sensor if the next 3 departures of defined lines are late or cancelled .... or in time. (Ref to "Alert Settings")
- there is a 2nd lovalace card for single card use. Means with big font so that you can put it on a screen or on an Amazon Show 15 (with the silk browser and the kiosk mode HA addon via Media Function from HA)
- ![20240301_152359025_iOS](https://github.com/Nisbo/another_mvg/assets/26260572/4a9133e4-4047-4fce-9240-0dbdbdf0e3c2)
- You have to add the resource ```/local/content-card-another-mvg-big.js``` as **JavaScripts-Modul** 
- improved error handling, additionally there will be an indicator on the card (Stop Name - nicht aktuell) if the data is outdated (older than 1 minute)
- fixed a bug where the sensor was updated with wrong data (thx to @msp1974 )

To update, replace all files with the new files, add the new resource mentioned above and restart HA.
Afterwards you have to clear the frontend cache on all devices.

28.05.2024 - Version 1.4.0
- improved error handling
- improved error reporting in the system log
- fixed an issue with CSS on some installations (possible problems with other addons)
- You can also use ```BAHN``` but this feature is not fully integrated and not enabled by default. There is also no special design / labeling available.
If you want to include it to your departure list, you can use this code:

```   transporttypes: "SBAHN,UBAHN,TRAM,BUS,REGIONAL_BUS,BAHN"```

To update, replace all files with the new files and restart HA.
Afterwards you have to clear the frontend cache on all devices.

# Credits
To all the guys in the Home Assistant forum for the help. 

To the MVG for the API. 

To other guys on github, were I was able to learn more about python code and Home Assistant. 

And to my best friend Google. ^^

# Disclaimer / Haftungsausschluss

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



