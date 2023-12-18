# another_mvg

Comming soon, another MVG Integration for Home Assistant

**This is an unofficial integration and does NOT belong to the MVG.**

**Only for private use (due to MVG rules, see bottom of this page).**



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



### Name of the table
```    name: "Pasing"``` **Optional, but strongly recommended**

Is the name of the table inside the card and will be used for the sensorname. It is **NOT** the name of the station for the API call.

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
BUS and REGIONAL_BUS are different. BUS is MVG and REGIONAL_BUS is MVV. But it looks like, in the API they mixed it for some lines. Just add both, to be save.
As mentioned above, by default all transportations are enabled. If you want to see only some, you have to use this parameter.

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
    hidedestination: "Deisenhofen,Holzkirchen,Grafing Bahnhof, Trudering, Ostbahnhof,Haar,Ebersberg"
  - platform: another_mvg
    name: "Pasing - alle Abfahrten"
    globalid: "de:09162:10"
    limit: 20
    doublestationnumber: "2"
    transporttypes: "SBAHN,BUS,REGIONAL_BUS"
  - platform: another_mvg
    name: "Olching und Eichenau"
    globalid: "de:09179:6110"
    globalid2: "de:09179:6180"
    hidedestination: "Mammendorf,Maisach,Geltendorf,Buchenau,Grafrath"
    limit: 15
    transporttypes: "SBAHN"
    doublestationnumber: "3"
```

# Browser View

![Screenshot_33](https://github.com/Nisbo/another_mvg/assets/26260572/c24cd351-2a44-4c5f-9250-5a4bb1f07450)

![Screenshot_34](https://github.com/Nisbo/another_mvg/assets/26260572/29985729-abfa-4049-8c4b-6b375303ceb1)

# Mobile App View

| Mobile App View  | Mobile App View |
| ------------- | ------------- |
| ![20231214_202848000_iOS](https://github.com/Nisbo/another_mvg/assets/26260572/17f56859-fe8c-440f-8168-dc491c42952e) | ![20231214_202831000_iOS](https://github.com/Nisbo/another_mvg/assets/26260572/a461b67e-9871-45bd-b98d-27e255d2350c) |


# Credits
To all the guys in the Home Assistant forum for the help. 

To the MVG for the API. 

To other guys on github, were I was able to learn more about python code and Home Assistant. 

And to my best friend Google. ^^

# MVG Disclaimer for the use of the data
German: ... Für private, nicht-kommerzielle Zwecke, wird eine gemäßigte Nutzung ohne unsere ausdrückliche Zustimmung geduldet. Jegliche Form von Data-Mining stellt keine gemäßigte Nutzung dar. Wir behalten uns vor, die Duldung grundsätzlich oder in Einzelfällen zu widerrufen. ...

English: ... For private, non-commercial purposes, moderate use is tolerated without our express consent. Any form of data mining does not constitute moderate use. We reserve the right to revoke our tolerance in principle or in individual cases. ...

Full (german) text can be found in the MVG impressum at the bottom.

https://www.mvg.de/impressum.html



