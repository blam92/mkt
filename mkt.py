# -*- coding: utf-8 -*-
import sys
import os
from flask import Flask, render_template, request, flash, redirect, url_for, make_response, send_from_directory
from werkzeug import secure_filename
import csv
import nltk
from nltk.corpus import stopwords
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from nltk.stem.porter import PorterStemmer

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['xls', 'csv', 'docx', 'xlsx'])
PATH_FOR_UPLOADS = './uploads'
PATH_FOR_DOWNLOAD = './download/grouped_key_words.csv'
app.secret_key = 'super_secret'



def allowed_file(filename):
	return ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

def agrupador(archivo):
    
    nltk.download('stopwords')
    stop = stopwords.words('spanish')
    stop.append('mas')
    #Instanceo Stemmer y CountVectorizer

    stemmer = PorterStemmer()
    analyzer = CountVectorizer(strip_accents='ascii',stop_words=stop).build_analyzer()

    #Armo la función que fitea ambas cosas
    def stemmed_words(kws):
        return (stemmer.stem(w) for w in analyzer(kws))

    
    #Leo Excel con Kws
    Data = pd.read_excel(archivo,skiprows=10)
    #Me quedo solo con la columna de Keywords del archivo
    kws = Data['Keyword']
    print('Excel Cargado')
    
    #Llamo a la funcion de arriba para que me fitee las KeyWords
    stem_vectorizer = CountVectorizer(analyzer=stemmed_words)
    a = stem_vectorizer.fit_transform(kws)
    
    #Armo el DataFrame del Vectorizer
    mat = pd.DataFrame(a.A, columns=stem_vectorizer.get_feature_names())
    print('Matriz Armada, ahora Looping...')

    #Reemplazo 1s por Nombre y 0s por NaN - ESTO TARDA
    for col_name in mat.columns:
        for row in range(len(mat)):
            if mat[col_name][row] == 1:
                mat[col_name][row] = str(col_name)
    print('Loop OK')
    
    
    #Ordeno las Columnas por frecuencia.
    freqs = [(word, a.getcol(idx).sum()) for word, idx in stem_vectorizer.vocabulary_.items()]
    
    sortedfreqs =  sorted (freqs, key = lambda x: -x[1])

    sortedcolumns = []
    for i in sortedfreqs:
        sortedcolumns.append(i[0])

    sorted_mat = mat[sortedcolumns]
    
    
    #Creo el Df para Grupos
    grupos = pd.DataFrame()
    print('Armando los Grupos...')

    #Le doy nombre a la Columna y aplico la función que va a traer solo los que no son nulos.
    grupos['AdGroup'] = sorted_mat.apply(lambda x: ' - '.join([unicode(y).title() for y in x if y != 0]), axis=1)

    #Agrego el grupo a la Data original
    grupos['Keyword'] = Data['Keyword']

    #Devuelvo Data
    grupos.to_excel('./download/grouped_key_words.xlsx')
    print('Las Kws y sus AdGroups se encuentran en > '+archivo+'_PythonAdGroups.xlsx')




################################# VIEWS ################################################
@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')

@app.route('/grouped_key_words', methods = ['GET', 'POST'])
def grouped_key_words():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect('index')

		f = request.files['file']
		if f.filename == '':
			flash('Please upload a file')
			return redirect('index')
		if f and allowed_file(f.filename):
			filename = secure_filename(f.filename)
			f.save(os.path.join(PATH_FOR_UPLOADS, filename))
			path = PATH_FOR_UPLOADS + '/' + filename
			return download(path)
		else:
			flash('Please check the file extension. Accepted file types: xls, csv')
			return redirect('index')
	return 'no post?'

@app.route('/download')
def download(file_path):
	agrupador(file_path)
	return send_from_directory(directory= 'download/', filename= 'grouped_key_words.xlsx')

def create_csv_string(dir_csv):
	csv_string = ''
	with open(dir_csv, 'rb') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			csv_string += row[0] + ', ' + row[1] + '\n'
	return csv_string