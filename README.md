Calistirma

**Metod 1 (Kolay):**

Ornek erkan_adana okulu icin asagidaki komutu calistirarak calisilan klasore butun dosyalar indirilir. 
USERNAME ve PASSWORD degiskenleri k12 uygulamasina giris yapilirken kullanilan kullanici adi ve sifredir. 

```
docker run --rm -it -v "$(pwd):/downloads" -e USERNAME=xxxxx -e PASSWORD=xxxx -e APP=erkan_adana ondercsn/k12scraper
```

Gelistirme icin : 

**Metod 2:**
1. docker-comopose.yml dosyasinda USERNAME, PASSWORD entryleri istenilen sekilde duzenlenir.
2. sonra klasor icinde "docker-compose up" komutu calistirilir.

**Metod 3:**
1. klasor icinde once "docker-compose --build" komutu calisitirilir.
2. build islemi bittikten sonra "docker compose run kullaniciadi sifresi" komutu calistirilir


