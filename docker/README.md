# Docker opzet 2.0

## Docker

### Prerequisites Docker

Om te controleren of je docker en docker-compose hebt kun je de volgende commando's gebruiken:

`docker version && docker ps -a`

`docker-compose version`

Zorg dat je versie niet te veel achterloopt omdat er dan features zijn die niet meer werken. 

De versie van docker op dit moment is 18.09 of nieuwer. Die van docker-compose is 1.23 of nieuwer.



### Quick start

Om het project lokaal op te zetten hoef je slechts 1 commando te gebruiken vanuit de root van het rest-api project:

`./docker/run-local.sh`



## HTTP reply on HTTPS request error

Deze error treedt op bij een docker installatie in Linux.
Het ICTU Vastgoed docker registry kent alleen maar HTTP, maak om bovenstaande error te voorkomen de file
`/etc/docker/daemon.json` aan met de inhoud:
```{
    "insecure-registries": ["www.docker-registry.vastgoed.ictu:5000"],
    "storage-driver": "overlay2"
}```
En herstart docker: `systemctl restart docker`