"""
Lista de artistas monitorizados por el Cubaton Music Bot.

Cada artista puede tener:
  - nombre        (obligatorio)
  - deezer_id     (recomendado, permite detección temprana en Deezer)
  - channel_id    (canal de YouTube Music)
  - channel_ids   (varios canales, opcional)
  - handle        (si se usa @usuario; el bot resuelve el channel_id al arrancar)

Para añadir un artista nuevo, basta con agregarlo a esta lista.
"""

ARTISTAS = [
    {
        "nombre": "Bebeshito",
        "deezer_id": "102097852",
        "channel_id": "UCpVfWS-cPOE2sYqsFuuP_Qg",
    },
    {
        "nombre": "Charly & Johayron",
        "deezer_id": "151878182",
        "channel_id": "UCnwEtOQyXJUUuBhcTgImdfQ",
    },
    {
        "nombre": "Dany Ome",
        "deezer_id": "51312522",
        "channel_id": "UCJQEm9t4KjDn-I8Fahf4Uqw",
    },
    {
        "nombre": "Wampi",
        "deezer_id": "53583382",
        "channel_id": "UCbfzw8u1lCwDMv443StJEOw",
    },
    {
        "nombre": "El Taiger",
        "deezer_id": "10733244",
        "channel_id": "UCoYtt7bGCV5RyUweyQgqQ4A",
    },
    {
        "nombre": "Ja Rulay",
        "deezer_id": "141683852",
        "channel_id": "UCcaU4COep7mj8kbXwS24JFQ",
    },
    {
        "nombre": "L Kimii",
        "deezer_id": "166612297",
        "channel_id": "UCMyQosiL8iVUtXPIm1UZJQg",
    },
    {
        "nombre": "El Dray",
        "deezer_id": "14445985",
        "channel_id": "UC4kpn8y8QXYXmyDn8HJKD8Q",
    },
    {
        "nombre": "Mauro y El Pitu",
        "deezer_id": "233465501",
        "channel_id": "UCvN1mRFfAfWYTiIkM70qUWA",
    },
    {
        "nombre": "Yirow Y El Tingo",
        "deezer_id": "246706542",
        "channel_id": "UCEq3_5h1Xi_vLbytP7OzuNA",
    },
    {
        "nombre": "Nany La Kbra",
        "deezer_id": "349727462",
        "channel_id": "UCG4lSNdNx_LuLnN2EW6uWwQ",
    },
    {
        "nombre": "Ya Ice Dilan",
        "deezer_id": "312201361",
        "channel_id": "UC9aJbR9Q8nscvZaMw_cH4Ww",
    },
    {
        "nombre": "Rey Tony",
        "deezer_id": "11269534",
        "channel_id": "UCDhExL0uVtumv_DEjPPq5qg",
    },
    {
        "nombre": "Baby Maikol",
        "deezer_id": "95702072",
        "channel_id": "UCP5R6Mgbk_bgtgzZguLNKdA",
    },
    {
        "nombre": "Payaso X Ley",
        "deezer_id": "100735422",
        "channel_id": "UCauTaqBvFqqqJTu3B4Wc1GA",
    },
    {
        "nombre": "Kaly Y Kowa",
        "deezer_id": "268432602",
        "channel_id": "UCSfR51myQhs2ZcdzrWo0Z4w",
    },
    {
        "nombre": "Wildey",
        "deezer_id": "8440220",
        "channel_id": "UCmFS-VSa4Wf3F1wdWS-8p_g",
    },
    {
        "nombre": "Wow Popy",
        "deezer_id": "94339592",
        "channel_id": "UCtFkN8UFxT_MuNdySlfuFuA",
    },
    {
        "nombre": "Talent Fuego",
        "deezer_id": "319839381",
        "channel_id": "UC0dVmcXfNa7lVeUBve3_FXw",
    },
    {
        "nombre": "Mawell",
        "deezer_id": "11269890",
        "channel_id": "UCL6P-jUDZEKBA-Lb6WFccWg",
    },
    {
        "nombre": "Harryson",
        "deezer_id": "305498",
        "channel_id": "UC2ihX5uoblnN4wsA-ayIAAA",
    },
    {
        "nombre": "El Chulo",
        "deezer_id": "1318293",
        "channel_id": "UCiT8VNdnpeYnCTPJZoqym9g",
    },
    {
        "nombre": "Fixty Ordara",
        "deezer_id": "148250982",
        "channel_id": "UCDHDCbVOQywsLCsCZ8PH-AA",
    },
    {
        "nombre": "El Kamel",
        "deezer_id": "13147221",
        "channel_id": "UCPnWcazEV7QM0H7qBx6NVXg",
    },
    {
        "nombre": "Velito el Bufón",
        "deezer_id": "154487672",
        "channel_id": "UCRA9cRfAJXuxDRcFnoB7pwg",
    },
    {
        "nombre": "Un Titico",
        "deezer_id": "14576461",
        "channel_id": "UCT2KiGFSPZIF3DR9UIN2fYw",
    },
    {
        "nombre": "Musteerifa",
        "deezer_id": "297753211",
        "channel_id": "UCiT8PzlQqtPC7lWFh3--4jw",
        "channel_ids": [
            "UCiT8PzlQqtPC7lWFh3--4jw",
            "UCUmbJ10w6Sljv-zIv0iQxNw",
        ],
    },
    {
        "nombre": "Los Dele",
        "deezer_id": "246797622",
        "channel_id": "UCe9SuCBefzhTyPCgiMMvcbA",
    },
    {
        "nombre": "Chocolate MC",
        "deezer_id": "1385931",
        "channel_id": "UCYVuThmAmbXxk1o9Un5Cc_w",
    },
    {
        "nombre": "El Chacal",
        "deezer_id": "357494",
        "channel_id": "UCJt4IsSmUjqTaamhCJoKK_g",
    },
    {
        "nombre": "El Micha",
        "deezer_id": "279482",
        "channel_id": "UCHhrMSqe_C1E_JBEz3mRlew",
    },
    {
        "nombre": "Yomil",
        "deezer_id": "5051695",
        "channel_id": "UCPfXwOpwRIbVsqqTsgt4i5g",
    },
    {
        "nombre": "Jacob Forever",
        "deezer_id": "1533735",
        "channel_id": "UCJ1-Pwsroy-gzMqlfKDF4Hg",
    },
    {
        "nombre": "Gente de Zona",
        "deezer_id": "279489",
        "channel_id": "UCl2KQVc_GFH081i7b9CJQug",
    },
    {
        "nombre": "La Diosa",
        "deezer_id": "4266566",
        "channel_id": "UChbVOQHgq01JoHY4axuWV0A",
    },
    {
        "nombre": "Seidy La Niña",
        "deezer_id": "59734012",
        "channel_id": "UCFqYfgj_7h3ZUkBnyYS-TFg",
    },
    {
        "nombre": "Yandito",
        "deezer_id": "104387432",
        "channel_id": "UCDBIl4Gc9VJjTSy8g_tve5w",
        "channel_ids": [
            "UCDBIl4Gc9VJjTSy8g_tve5w",
            "UCcXUh7Nrgx2uDJxBrgj5XMQ",
        ],
    },
    {
        "nombre": "Yeyito DK",
        "deezer_id": "262957411",
        "channel_id": "UCrP6x4goKf26TaWWHbJM0ZA",
        "channel_ids": [
            "UCrP6x4goKf26TaWWHbJM0ZA",
            "UCwOsxuuwyt--PMDxAXdYYLQ",
            "UCcr2yCU1UnvRIomc56WxFgA",
        ],
    },
    # Estos se configuran por @usuario; el bot obtiene su channel_id
    # al arrancar (ver resolver_handles_artistas).
    {
        "nombre": "Anyelazo",
        "deezer_id": "262524691",
        "handle": "@anyelazo_oficial",
    },
    {
        "nombre": "El Yohas",
        "deezer_id": "269045212",
        "handle": "@el_yohas",
    },
    {
        "nombre": "El Ankla",
        "deezer_id": "64307332",
        "handle": "@elanklaofficial",
    },
    {
        "nombre": "Dj Honda",
        "handle": "@hondadj2026",
    },
    # Artista solo con Deezer (sin canal de YouTube Music configurado).
    {
        "nombre": "Ozunaje",
        "deezer_id": "298508751",
    },
]
