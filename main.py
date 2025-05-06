import requests, sqlite3, datetime, itertools # type: ignore

global m_nosaukums
m_nosaukums = ["JANVĀRIS", "FEBRUĀRIS", "MARTS", "APRĪLIS", "MAIJS", "JŪNIJS", "JŪLIJS", "AUGUSTS", "SEPTEMBRIS", "OKTOBRIS", "NOVEMBRIS", "DECEMBRIS"]

#klases izveide 
class Vardadiena:
    def __init__(self, id, vards, datums):
        self.id = id
        self.vards = vards
        self.datums = datums
        self.uzvards = str()

    #getter vārdam
    @property
    def vards(self):
        return self._vards
    
    #setter vārdam
    @vards.setter
    def vards(self, vards):
        if not vards.isalpha() or vards == '':
            raise ValueError('Nederīgs vārds!')
        self._vards = vards

    #datu izvade
    def __str__(self):
        if self.uzvards == '':
            return f'\nVārds: {self.vards}\nVārda dienas datums: {self.datums.day}. {m_nosaukums[self.datums.month-1]}'
        else: 
            return f'\nVārds: {self.vards}\nUzvārds: {self.uzvards}\nVārda dienas datums: {self.datums.day}. {m_nosaukums[self.datums.month-1]}'

    def pievienot_uzvardu(self, uzvards):
        self.uzvards = uzvards

#atvasinātās klases izveide
class Vardadiena_grupas(Vardadiena):
    def __init__(self, id, vards, datums, grupa):
        super().__init__(id, vards, datums)
        self.grupa = grupa
        self.uzvards = str()

    def pievienot_uzvardu(self, uzvards):
        self.uzvards = uzvards

def main():
    ievades_piekļuve = True
    vardadienas = []
    vardadienas_grupas = []
    grupas = []
    #datubāzes savienojums un izveide, ja datubāze neeksistē
    datubaze = sqlite3.connect('vardadienas.db')
    kursors = datubaze.cursor()
    kursors.execute('''CREATE TABLE IF NOT EXISTS grupas 
                            (grupas_id integer NOT NULL UNIQUE, grupa text NOT NULL, PRIMARY KEY(grupas_id AUTOINCREMENT))''')

    kursors.execute('''CREATE TABLE IF NOT EXISTS vardadienas 
                                    (persona_id integer NOT NULL UNIQUE, datums text NOT NULL, vards text NOT NULL, uzvards text, grupas_id integer NOT NULL, PRIMARY KEY(persona_id AUTOINCREMENT), FOREIGN KEY(grupas_id) REFERENCES grupas(grupas_id))''')

    #vārda dienu api piekļuve
    vd_pieprasijums = requests.get('https://www.jsonkeeper.com/b/RPXI')
    vd_api = vd_pieprasijums.json()

    #svētku api piekļuve
    s_pieprasijums = requests.get('https://openholidaysapi.org/PublicHolidays?countryIsoCode=LV&validFrom=2025-01-01&validTo=2025-12-31&languageIsoCode=LV&subdivisionCode=LV-EN')
    s_api = s_pieprasijums.json()

    #datubāzes nolasīšana
    for i in kursors.execute('''SELECT * FROM grupas'''):
        grupas.append(i[1])
    for i in kursors.execute('''SELECT * FROM vardadienas'''):
        if not i[4]:
            vardadienas.insert(0, Vardadiena(i[0], i[2], datetime.date(2025, int(i[1][i[1].index('.')+1:-1]), int(i[1][:i[1].index('.')]))))
            if i[3]:
                vardadienas[0].pievienot_uzvardu(i[3])
        elif i[4]:
            vardadienas_grupas.insert(0, Vardadiena_grupas(i[0], i[2], datetime.date(2025, int(i[1][i[1].index('.')+1:-1]), int(i[1][:i[1].index('.')])), grupas[int(i[4])-1]))
            if i[3]:
                vardadienas_grupas[0].pievienot_uzvardu(i[3])
    
    print('\n## VĀRDA DIENU KALKULATORS ##\n')
    print('Funkcijas:\n"-a" - atrast personas vārda dienu\n"-i" - izvēlēties personu no kontaktiem\n"-u" - pievienot vai mainīt izvēlētās personas uzvārdu\n"-g" - pievienot vai mainīt izvēlētās personas piederību grupai\n"-d" - dzēst personu no kontaktiem\n"-k" - atvērt kontaktu grāmatu\n"-b" - beigt programmas darbību\n')

    while True:
        #funkciju ievade
        f_ievade = input().strip()
        #vārda dienas atrašanas funkcija
        if f_ievade == '-a':
            #vārda ievade
            ievade = input('Ievadi vārdu: ').title().strip()

            #vārda dienas datuma meklētājs
            for meness in range(len(vd_api)):
                for diena in vd_api[meness]:
                    for vards in vd_api[meness][diena]:
                        if ievade == vards:
                            #datuma saglabāšana
                            datums=datetime.date(2025, int(meness)+1, int(diena)+1)
                            print(f'{int(diena)+1}. {m_nosaukums[meness]}')

            #svētku datumu salīdzinātājs
            try:
                for kategorija in s_api:
                    #svētku izvade, kas sakrīt ar vārda dienu datumu
                    if str(kategorija['startDate'])==str(datums):
                        print(f'Šajā datumā svin {kategorija['name'][0]['text']}!')
            except UnboundLocalError:
                #gadījumā, kad API nav atrasts vārds, tiek atlasīta neparasto vārdu vārda diena
                print('22. MAIJS')
                print('Šajā datumā vārda dienu svin visi, kuriem ir neparasti vārdi!')
                datums = datetime.date(2025, 5, 22)

            #vaicājums saglabāt, saglabāšanas algoritms
            s_ievade = input('Vai vēlies saglabāt vārdu kontaktos?: ').lower().strip()
            if s_ievade == 'jā' or s_ievade == 'ja' or s_ievade == 'j' or s_ievade == 'yes' or s_ievade == 'y' or s_ievade == '1':
                for i in itertools.chain(vardadienas, vardadienas_grupas):
                    if ievade == i.vards and i.uzvards == '':
                        #gadījumā, kad atrasta persona ar tādu pašu vārdu bez uzvārda, saglabāšanas atcelšana
                        print('Šāda persona jau ir kontaktos!\nJa vēlaties pievienot personu ar tādu pašu vārdu, lūdzu pievienojiet uzvārdu šī vārda personai!')
                        ievades_piekļuve = False
                        break
                    if ievade == i.vards:
                        #gadījumā, kad atrasta persona ar tādu pašu vārdu ar uzvārdu, vaicājums pievienot uzvārdu pie jaunā kontakta
                        print('Persona ar šo vārdu jau ir kontaktos!')
                        u_ievade = input('Pievienojiet uzvārdu, lai personu varētu atpazīt!: ')
                        if i.uzvards == u_ievade:
                            #gadījumā, kad atrasta persona ar tādu pašu vārdu un uzvārdu, saglabāšanas atcelšana
                            print('Persona ar šo vārdu un uzvārdu jau atrodas kontaktos!')
                        else:
                            #jaunas personas pievienošana kontaktiem, saglabāšana ar vārdu un uzvārdu
                            vardadienas.insert(0, Vardadiena(len(vardadienas)+len(vardadienas_grupas)+1, ievade, datums))
                            vardadienas[0].pievienot_uzvardu(u_ievade)
                            kursors.execute(f'''INSERT INTO vardadienas VALUES
                                                ({vardadienas[0].id},'{datums.day}.{datums.month}.','{ievade}','{u_ievade}', '')''')
                            datubaze.commit()
                            print('Persona saglabāta!')
                        ievades_piekļuve = False
                        break
                if ievades_piekļuve:
                    #personas saglabāšana kontaktos
                    vardadienas.insert(0, Vardadiena(len(vardadienas)+len(vardadienas_grupas)+1, ievade, datums))
                    kursors.execute(f'''INSERT INTO vardadienas VALUES
                                        ({vardadienas[0].id},'{datums.day}.{datums.month}.','{ievade}','','')''')
                    datubaze.commit()
                    print('Persona saglabāta!')
                del ievade
                del datums
                ievades_piekļuve = True
            else:
                #gadījums, kad saglabāšana nav izvēlēta
                pass
                del ievade
                del datums

        #kontakta izvēles funkcija  
        elif f_ievade == '-i':
            try:
                izveles_skaits = 0
                v_ievade = input('Ievadiet personas vārdu: ').title().strip()
                #pārbaude, vai nav vairāki kontakti ar tādu pašu vārdu
                for i in itertools.chain(vardadienas, vardadienas_grupas):
                    if i.vards == v_ievade:
                        izveles_skaits += 1
                        izvele = i
                if izvele != '' and izveles_skaits == 1:
                    #personas izvēle
                    print('Persona izvēlēta!')
                elif izvele != '' and izveles_skaits > 1:
                    #gadījumā, kad ir vairākas personas ar tādu pašu vārdu, vaicājums uzvārdam
                    u_ievade = input('Atrastas vairākas personas ar šo vārdu!\nIevadiet personas uzvārdu: ')
                    for i in itertools.chain(vardadienas, vardadienas_grupas):
                        if i.uzvards == u_ievade:
                            izvele = i
                    print('Persona izvēlēta!')

            except UnboundLocalError:
                #kļūdas paziņojums gadījumā, kad nav atrasta meklētā persona kontaktos
                print('Kontakts neeksistē!')
        
        #kontakta uzvārda pievienošanas, mainīšanas funkcija 
        elif f_ievade == '-u':
            try:
                u_ievade = input('Ievadiet uzvārdu: ')
                #pārbaude, vai nav vēl kāda persona ar tādu pašu vārdu un uzvārdu, to mainot personai
                for i in itertools.chain(vardadienas, vardadienas_grupas):
                    if i.uzvards == u_ievade and i != izvele:
                        ievades_piekļuve = False
                        print('Persona ar šādu vārdu un uzvārdu jau eksistē!')
                        break
                #personas uzvārda nomainīšana          
                if ievades_piekļuve and izvele.uzvards != '':
                    izvele.pievienot_uzvardu(u_ievade)
                    kursors.execute(f'''UPDATE vardadienas SET uzvards = '{u_ievade}' WHERE persona_id = '{izvele.id}' ''')
                    datubaze.commit()
                    print('Personai nomainīts uzvārds!')
                #personas uzvārda pievienošana
                elif ievades_piekļuve:
                    izvele.pievienot_uzvardu(u_ievade)
                    kursors.execute(f'''UPDATE vardadienas SET uzvards = '{u_ievade}' WHERE persona_id = '{izvele.id}' ''')
                    datubaze.commit()
                    print('Personai pievienots uzvārds!')
                ievades_piekļuve = True
            except UnboundLocalError:
                #kļūdas paziņojums gadījumā, kad nav izvēlēta neviena persona no kontaktiem
                print('Nav izvēlēta persona!')

        #kontakta grāmatas pārskatījuma funkcija 
        elif f_ievade == '-k':    
            if not vardadienas and not vardadienas_grupas:
                #pārbaude, vai kontaktu grāmata nav tukša  
                print('Nav kontaktu!')
            elif not vardadienas_grupas:
                #kontaktu grāmatas izvade, ja nav izveidotas grupas
                print('Kontaktu grāmata:')
                for i in vardadienas:
                    print(i)
            elif vardadienas_grupas:
                #kontaktu grāmatas izvade arm grupām
                print('Kontaktu grāmata:')
                for i in grupas:
                    print(f'\nGrupa "{i}":')
                    for k in vardadienas_grupas:
                        if k.grupa == i:
                            print(k)
                if vardadienas:
                    print('\nPārējās personas:')
                    for i in vardadienas:
                        print(i)

        #grupu izveides un mainīšanas funkcija 
        elif f_ievade == '-g':
            try:
                g_id = int()
                g_ievade = input('Ievadiet grupas nosaukumu: ').title().strip()
                if g_ievade in grupas:
                    #ja grupa eksistē, tad piešķir grupu personai, pārnes uz grupas klasi
                    vardadienas_grupas.insert(0, Vardadiena_grupas(izvele.id, izvele.vards, izvele.datums, g_ievade))
                    for i in range(len(grupas)):
                        if g_ievade == grupas[i]:
                            g_id = i+1
                    kursors.execute(f'''UPDATE vardadienas SET grupas_id = {g_id} WHERE persona_id = '{izvele.id}' ''')
                    datubaze.commit()
                    
                    if izvele.uzvards:
                        #ja izvēlētajai personai ir uzvārds, tad pievieno uzvārdu grupu saraksta
                        vardadienas_grupas[0].pievienot_uzvardu(izvele.uzvards)
                    print('Grupa pievienota izvēlētajai personai!')
                else:
                    #ja grupa neeksistē, to izveido un tad piešķir grupu personai
                    grupas.append(g_ievade)
                    vardadienas_grupas.insert(0, Vardadiena_grupas(izvele.id, izvele.vards, izvele.datums, g_ievade))
                    kursors.execute(f'''INSERT INTO grupas VALUES ({len(grupas)},'{g_ievade}')''')
                    datubaze.commit()
                    kursors.execute(f'''UPDATE vardadienas SET grupas_id = {len(grupas)} WHERE persona_id = '{izvele.id}' ''')
                    datubaze.commit()
                    if izvele.uzvards:
                        #ja izvēlētajai personai ir uzvārds, tad pievieno uzvārdu grupu saraksta 
                        vardadienas_grupas[0].pievienot_uzvardu(izvele.uzvards)
                    print('Grupa izveidota un pievienota izvēlētajai personai!')
                for i in range(len(vardadienas)):
                    if vardadienas[i] == izvele:
                        #pēc izvēlētās personas pievienošanu grupas klasei, to izdzēš no regulāro personu saraksta
                        del g_id
                        del vardadienas[i]
                        break  
            except UnboundLocalError:  
                #kļūdas paziņojums gadījumā, kad nav izvēlēta neviena persona no kontaktiem
                print('Nav izvēlēta persona!')

        #kontakta dzēšanas funkcija
        elif f_ievade == '-d':
            try:
                izveles_skaits = 0
                #kontakta dzēšana
                for i in range(len(vardadienas)):
                    if vardadienas[i] == izvele:
                        kursors.execute(f'''DELETE FROM vardadienas WHERE persona_id = '{izvele.id}' ''')
                        datubaze.commit()
                        del vardadienas[i]
                        del izvele
                        break
                for i in range(len(vardadienas_grupas)):
                    if vardadienas_grupas[i] == izvele:
                        kursors.execute(f'''DELETE FROM vardadienas WHERE persona_id = '{izvele.id}' ''')
                        datubaze.commit()
                        del vardadienas_grupas[i]
                        del izvele
                        break
                print('Persona dzēsta!')
            except UnboundLocalError:
                #kļūdas paziņojums gadījumā, kad nav izvēlēta neviena persona no kontaktiem
                print('Nav izvēlēta persona!')
        
        #programmas darbības beigšanas funkcija
        elif f_ievade == '-b':
            datubaze.close()
            break
        else:
            #kļūdas paziņojums gadījumā, kad nav atrasta derīga funkcija
            print('Funkcija netika atrasta!')

if __name__ == '__main__':
    main()