# promCliUtil

## promCliUtil code structure

### promSession Object

| Method			| Description 	|
| ---				| ---			|
| startup			|	|
| shutdown			|	|
| writeCommand		|	|
| captureImage		|	|	
| captureHDRImage	|	|
| captureVideo		|	|
| captureHDRVideo	|	|
| __openMeta		|	|
| __writeMeta		|	|
| __closeMeta		|	|

| Attribute			| Description 	|
| ---				| ---			|
| capSet			| captureSettings object	|

### captureSettings Object
| Method			| Description 	|
| ---				| ---			|
| setComp			| Compare Settings|
| listCmds			|				|
| imgCmd			| getBWSorted or getDCSSorted|

| Attribute			| Description 	|
| ---				| ---			|
| mode				| 0 = 2D, 1 = 3D|
| pidelay			| 0 or 1		|
| exposuretime		| ms			|
| modFreq			| 0 = 24 MHz, 1 = 12 MHz|

---
## prom-cli commands

### prom-cli command format
`/build/prom-cli -a {command} -i {camnum}`

### prom-cli command list

| Command			| Parameter		| Description	|
| ---				| ---			| ---			|
| `"getBWSorted"`	| None			| Take 2D/Grayscale Image (must be in 2D mode)	|
| `"getDCSSorted"`	| None			| Take 3D/DCS Image (must be in 3D mode)		|
| `"setIntegrationTime2D {n}"`  | n=ms of 2D exposure time	| Set 2D exposure time	|
| `"setIntegrationTime3D {n}"`	|	|	|
| `"setEnableImaging {0/1}"`  	|	|	|
| `"loadConfig {0/1}"`  		|	|	|
|`"setModulationFrequency {0/1}"`    |	|	|
|`"enablePiDelay {0/1}"`  	|	|	|



### prom-cli initialization

