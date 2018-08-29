photos = {
"rood": "http://alexvdg.nl/cards/rood.jpg",
"geel": "http://alexvdg.nl/cards/geel.jpg",
"aubergine": "http://alexvdg.nl/cards/aubergine.jpg",
"groen": "http://alexvdg.nl/cards/groen.jpg",
"oui": "http://alexvdg.nl/cards/oui.jpg",
"superrood": "http://alexvdg.nl/cards/superrood.jpg",
"ussr": "http://alexvdg.nl/cards/ussr.jpg",
"baer": "http://alexvdg.nl/cards/baer.jpg",
"exodia": "http://alexvdg.nl/cards/exodia.jpg",
"margot": "http://alexvdg.nl/cards/margot.jpg",
"meshuggah": "http://alexvdg.nl/cards/messhugah.png",
"negerpiemel": "http://alexvdg.nl/cards/negerpiemel.jpg",
"ruiten10": "http://alexvdg.nl/cards/ruiten%20tien.png",
"slomp": "http://alexvdg.nl/cards/slomp.jpg",
"slowpoke": "http://alexvdg.nl/cards/slowpoke.jpg",
"starcraft": "http://alexvdg.nl/cards/starcraft.jpg",
"traphole": "http://alexvdg.nl/cards/traphole.jpg",
"trump": "http://alexvdg.nl/cards/trump.jpg",
"wat": "http://alexvdg.nl/cards/wat.jpg",
"gloen": "http://alexvdg.nl/cards/gloen.jpg",
"rutte": "http://alexvdg.nl/cards/rutte.jpg",
}

introtext = """Hoi mijn naam is Henk, ik ben een bot die allerlei dingen kan doen.
Voor een overzicht van wat ik allemaal kan, vraag aan me "Henk wat kun je allemaal?" (of /help). Als je mijn maker niet kent, gebruik me dan alsjeblieft ook niet, daar ben ik niet voor gemaakt :)"""

helptext = """Ik kan allemaal dingen doen voor je door me het netjes te vragen, dat wil zeggen door een zin te beginnen met "hey/hoi/haai/sup Henk" (of gewoon alleen Henk). Mijn nuttige commando's hebben ook een saaie variant die begint met een slash (/). De lijst van dingen waar ik op reageer is niet compleet, experimenteer maar :)

Een weerbericht geven: /weather
"Henk, wat voor weer wordt het?"

Het menu van de Refter voor vandaag ophalen: /refter
"Henk, wat heeft de Refter vandaag?"

Informatie geven over berichten stats: /stats
"Henk, hoeveel berichten zijn er?", "Hey Henk, wie hebben er gespamd?"

Zoeken op wikipedia: /wiki <text>
"wat is <text>", "definieer <text>"
Bijvoorbeeld: Henk, wat is Nederland?

Polls aanmaken: /poll polltext | optie1 | optie2 | optie3

Dingen voor je berekenen: /calc <expression>
"bereken <stuff>", "hoeveel is <stuff>"
Bijvoorbeeld: Henk, bereken 38*3^(5+ln(sin(pi/2)))


Je kan me ook nieuwe responses aanleren.
Voor meer informatie type /learnhelp

Naast dit alles probeer ik te reageren op andere vragen die je me stelt ;)"""

helpsilent = """Ik sta momenteel op stil (/setsilent 1), dit betekent dat alleen mijn saaie commando's werken.
Om alles te activeren zet /setsilent 0
Wat wel nog werkt:
Zoeken op wikipedia: /wiki <text>
Informatie geven over berichten stats: /stats
Dingen voor je berekenen: /calc <expression> """

learnhelp = """
/learn <query> -> <response1> | <response2> | ... | <responseN>
Voorbeeld: /learn Henk, hoe gaat het met je? -> Goed hoor | Niet zo goed
/myresponses - Laat je zien welke responses je mij allemaal aangeleerd hebt (je kan alleen maar je eigen responses zien)
/deleteresponse n - Verwijdert response n (nummer zichtbaar bij /myresponses)

/alias <query1> | <query2> | ... | <queryN>
Dit leert mij dat ik op zin1 tot en met zinN op dezelfde manier kan reageren
/myaliases - Zie /myresponses
/deletealias n - Zie /deleteresponse n
/showalias <query> - Laat zien welke aliases ik allemaal ken voor <query>

Tip: Doe dit in een privechat om mensen te verrassen met mijn nieuwe kennis :)

query wordt gestript van hoofdletters, vraagtekens, uitroeptekens en een punt op het einde van de query. Verder wordt ", " vervangen met " ".
De responses mogen in principe alle soorten tekst bevatten die Telegram aankan en worden ook zo weergegeven.
In de responses wordt !name vervangen met de naam van de afzender.
De eerste keer dat ik query zie zeg ik een van de responses (of een andere response die ik geleerd heb bij die query).
De keren daarna heb ik minder zin om het te zeggen, hoewel het na een tijdje wel weer leuk wordt om te zeggen ;)
query mag niet een standaardresponse zijn (ik zeg het je als je dit probeert), het mag ook niet beginnen met een slash.

Je kan ook responses toevoegen aan speciale categorieen. Dit doe je door query te laten beginnen met $.
Toegestane categorieën zijn: 
$hi - Hoe ik kan reageren op mensen die me begroeten
$question_degree - Voor ja/nee vragen
$question_amount - Voor hoeveelheden
$question_opinion - Voor mijn mening
$question_(why/what/where/how/when/who/which/waarvoor) - hopelijk vanzelfsprekend
$je_moeder - beschrijvingen van je moeder
$wiki_failure - Wat ik kan zeggen als wikipedia niet mee werkt
$math_error - Als ik dom ben
$cuss_out - Wat ik kan zeggen als iemand me beledigd
$negative_response - willekeurige negatieve dingen die ik soms zeg
"""
