# Keittokirja

## Sovelluksen toiminnot

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan reseptejä.
- Käyttäjä näkee sovellukseen lisätyt reseptit.
- Käyttäjä pystyy etsimään reseptejä hakusanalla.
- Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät reseptit.
- Käyttäjä pystyy valitsemaan reseptille yhden tai useamman luokittelun (ruokalaji ja valmistusaika).
- Käyttäjä pystyy antamaan reseptille arvion (arvosana ja kommentti). Reseptin sivulla näkyy annetut arviot ja arvioiden keskiarvo.

## Sovelluksen nykyinen tilanne

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään.
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan reseptejä.
- Käyttäjä näkee lisätyt reseptit ja pystyy etsimään niitä hakusanalla.
- Luokittelut, arviot ja käyttäjäsivut ovat vielä tekemättä.

## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut:

```
$ sqlite3 database.db < schema.sql
```

Käynnistä sovellus:

```
$ flask run
```
Sovellus avautuu selaimessa osoitteessa http://127.0.0.1:5000