# -*- coding: utf-8 -*-

import tkMessageBox
import ttk
from Tkinter import *

import CompleteProcessingDrought as completeDrought
import DroughtDataManualUpload as ddup
import FloodDataManualUpload as fdup


class AppSPARC:
    def __init__(self, finestra):

        self.dbname = "geonode-imports"
        self.user = "geonode"
        self.password = "geonode"
        self.lista_amministrazioni = None

        finestra.geometry("450x310+30+30")

        self.area_messaggi = Text(finestra, background="black", foreground="green")

        self.area_messaggi.place(x=18, y=30, width=282, height=275)

        self.scr = Scrollbar(finestra, command=self.area_messaggi.yview)
        self.scr.place(x=8, y=30, width=10, height=275)
        self.area_messaggi.config(yscrollcommand=self.scr.set)

        self.collect_codes_country_level()
        self.box_value_adm0 = StringVar()
        self.box_adm0 = ttk.Combobox(finestra,
                                     textvariable=self.box_value_adm0)
        self.box_adm0['values'] = self.lista_paesi
        self.box_adm0.current(0)
        self.box_adm0.place(x=16, y=2, width=285, height=25)

        # SECTION FOR FLOOD CALCULATION
        # SECTION FOR FLOOD CALCULATION
        frame_flood = Frame(finestra, height=32, width=400, bg="blue")
        frame_flood.place(x=305, y=30, width=140, height=70)

        self.button_flood = Button(finestra,
                                   text="Flood Assessment",
                                   fg="blue")
        self.button_flood.bind('<Button-1>',
                               lambda scelta: scegli_calcolo("flood"))
        self.button_flood.place(x=310, y=35, width=130, height=25)

        self.button_flood_upload = Button(finestra,
                                          text="Upload Data Manually",
                                          fg="blue",
                                          command=self.flood_upload)
        self.button_flood_upload.place(x=310, y=70, width=130, height=25)
        # SECTION FOR FLOOD CALCULATION
        # SECTION FOR FLOOD CALCULATION

        # SECTION FOR DROUGHT CALCULATION
        # SECTION FOR DROUGHT CALCULATION
        frame_drought = Frame(finestra, height=80, width=400, bg="maroon")
        frame_drought.place(x=305, y=105, width=140, height=70)

        self.button_drought = Button(finestra,
                                     text="Drought Assessment",
                                     fg="maroon")
        self.button_drought.place(x=310, y=110, width=130, height=25)
        self.button_drought.bind('<Button-1>',
                                  lambda scelta: scegli_calcolo("drought"))

        self.button_drought_upload = Button(finestra,
                                            text="Upload Data Manually",
                                            fg="maroon",
                                            command=self.drought_upload)
        self.button_drought_upload.place(x=310, y=145, width=130, height=25)
        # SECTION FOR DROUGHT CALCULATION
        # SECTION FOR DROUGHT CALCULATION


        def scegli_calcolo(scelta):

            attivo_nonAttivo = self.var_check.get()
            paese = self.box_value_adm0.get()

            if attivo_nonAttivo == 0 and scelta == 'flood':
                self.national_calc_flood(paese)
            elif attivo_nonAttivo == 1 and scelta == 'flood':
                verifica = tkMessageBox.askyesno("Warning",
                                                 "Ci vediamo domani...!!" +
                                                 "Continuo?")
                if verifica:
                    self.world_calc_flood()
                else:
                    pass

            if attivo_nonAttivo == 0 and scelta == 'drought':
                self.national_calc_drought(paese)
            elif attivo_nonAttivo == 1 and scelta == 'drought':
                verifica = tkMessageBox.askyesno("Warning",
                                                 "Ci vediamo domani...!!" +
                                                 "Continuo?")
                if verifica:
                                    self.world_calc_drought()
                else:
                    pass

              
        def attiva_disattiva():

            attivo_nonAttivo = self.var_check.get()
            if attivo_nonAttivo == 0:
                self.box_adm0.config(state='normal')
                self.button_flood_upload.config(state='normal')
                self.button_drought_upload.config(state='normal')
            else:
                self.box_adm0.config(state='disabled')
                self.button_flood_upload.config(state='disabled')
                self.button_drought_upload.config(state='disabled')

        self.var_check = IntVar()
        self.check_all = Checkbutton(finestra,
                                     text="All Countries",
                                     variable=self.var_check,
                                     command=attiva_disattiva)
        self.check_all.place(x=310, y=5, width=120, height=25)

        finestra.mainloop()

    def collect_codes_country_level(self):

        paesi = completeDrought.ManagePostgresDBDrought(self.dbname, self.user, self.password)
        self.lista_paesi = paesi.all_country_db()

    def national_calc_drought(self, paese):

        db_conn_drought = completeDrought.ManagePostgresDBDrought(self.dbname,
                                                                  self.user,
                                                                  self.password)
        lista_admin2 = db_conn_drought.admin_2nd_level_list(paese)

        for amministrazione in lista_admin2[1].iteritems():
            code_admin = amministrazione[0]
            nome_admin = amministrazione[1]['name_clean']

            db_conn_drought.file_structure_creation(nome_admin, code_admin)
            newDroughtAssessment = completeDrought.HazardAssessmentDrought(self.dbname,
                                                                           self.user,
                                                                           self.password)
            newDroughtAssessment.extract_poly2_admin(paese, nome_admin, code_admin)

            section_pop_raster_cut = newDroughtAssessment.cut_rasters_drought(paese, nome_admin, code_admin)

            if section_pop_raster_cut == "sipop":
                self.area_messaggi.insert(INSERT, "Population clipped....")
            elif section_pop_raster_cut == "nopop":
                self.area_messaggi.insert(INSERT, 
                    "Population raster not available....")
                sys.exit()

        dizio_drought = db_conn_drought.collect_drought_population_frequencies_frm_dbfs()
        self.area_messaggi.insert(INSERT, "Data Collected\n")
        adms = set()
        for chiave, valori in sorted(dizio_drought.iteritems()):
            adms.add(chiave.split("-")[1])
        insert_list = db_conn_drought.prepare_insert_statements_drought_monthly_values(adms, dizio_drought)[2]
        self.area_messaggi.insert(INSERT, "Data Ready for Upload in DB\n")

        if db_conn_drought.check_if_monthly_table_drought_exists() == '42P01':
            db_conn_drought.create_sparc_drought_population_month()
            db_conn_drought.insert_drought_in_postgresql(insert_list)

        if db_conn_drought.check_if_monthly_table_drought_exists() == 'exists':
            self.area_messaggi.insert(INSERT, "Table Drought Exist\n")
            db_conn_drought.clean_old_values_month_drought(paese)
            db_conn_drought.save_changes()
            db_conn_drought.insert_drought_in_postgresql(insert_list)

        db_conn_drought.save_changes()
        db_conn_drought.close_connection()
        self.area_messaggi.insert(INSERT, "Data for " + paese + " stored db\n")

    def world_calc_drought(self):

        paesi = self.lista_paesi
        for paese in paesi:
            self.national_calc_drought(paese)

    def drought_upload(self):        
        
        paese = self.box_value_adm0.get()
        
        proj_dir = "c:/sparc/projects/drought/"
        dirOutPaese = proj_dir + paese

        raccogli_da_files_anno = ddup.collect_drought_poplation_frequencies_frm_dbfs(dirOutPaese)
        adms = set()
        for chiave, valori in sorted(raccogli_da_files_anno.iteritems()):
            adms.add(chiave.split("-")[1])
        raccolti_anno = ddup.prepare_insert_statements_drought_monthly_values(paese, adms, raccogli_da_files_anno)
        risultato = ddup.insert_drought_in_postgresql(paese, raccolti_anno[2])
        self.area_messaggi.insert(INSERT, risultato)

    def national_calc_flood(self, paese):

        import CountryCalculationsFlood

        calcolo = CountryCalculationsFlood.data_processing_module_flood(paese)
        self.area_messaggi.insert(INSERT, calcolo)

        data_upload = CountryCalculationsFlood.data_upload_module_flood(paese)
        self.area_messaggi.insert(INSERT, data_upload)

    def world_calc_flood(self):

        paesi = self.lista_paesi
        for paese in paesi:
            self.national_calc_flood(paese)

    def flood_upload(self):

        paese = self.box_value_adm0.get()

        proj_dir = "c:/sparc/projects/floods/"
        dirOutPaese = proj_dir + paese
        fillolo = dirOutPaese + "/" + paese + ".txt"

        raccogli_da_files_anno = fdup.collect_annual_data_byRP_from_dbf_country(dirOutPaese)
        adms = []
        for raccolto in raccogli_da_files_anno:
            adms.append(raccolto)
        raccolti_anno = fdup.process_dict_with_annual_values(paese,
                                                             adms,
                                                             raccogli_da_files_anno,
                                                             fillolo)
        fdup.inserisci_postgresql(paese, raccolti_anno[2])
        raccolti_mese = fdup.raccogli_mensili(fillolo)
        risultato = fdup.inserisci_postgresql(paese, raccolti_mese)
        self.area_messaggi.insert(INSERT, risultato)

root = Tk()
root.title("SPARC Flood and Drought Assessment")
app = AppSPARC(root)