#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import hashlib
import base64
import copy
import sys
import os

# Key is URI, value is hash
memoized_sha256_hashes = {}

def get_recursive_file_list( directory, extension ):
    return [ os.path.join(dp, f) for dp, dn, filenames in os.walk( directory ) for f in filenames if os.path.splitext(f)[1] == '.' + extension ]

def get_soup_from_file( filename ):
    file_handler = open( filename, 'r' )
    file_contents = file_handler.read()
    file_handler.close()
    soup = BeautifulSoup( file_contents )
    return soup

def is_external_url( url ):
    if str( url ).startswith( 'http://' ):
        return True
    if str( url ).startswith( 'https://' ):
        return True
    if str( url ).startswith( '://' ):
        return True
    if str( url ).startswith( '//' ):
        return True
    return False

def is_external_javascript( script_element ):
    return script_element.has_attr( 'src' ) and is_external_url( script_element.get( 'src' ) )

def is_external_stylesheet( style_element ):
    return style_element.has_attr( 'href' ) and is_external_url( style_element.get( 'href' ) )

def get_sri_protected_html( soup ):
    return_html = str( soup )
    stylesheets = soup.findAll( 'link', { 'rel': 'stylesheet' } )
    stylesheets = filter( is_external_stylesheet, stylesheets )

    for stylesheet in stylesheets:
        old_stylesheet = str( stylesheet )
        new_stylesheet = stylesheet
        new_stylesheet['integrity'] = get_integrity_hash( stylesheet.get( 'href' ) )
        new_stylesheet['crossorigin'] = 'anonymous'
        return_html = return_html.replace( old_stylesheet, str( new_stylesheet ) )

    scripts = soup.findAll( 'script' )
    scripts = filter( is_external_javascript, scripts  )

    for script in scripts:
        old_script = str( script )
        new_script = script
        new_script['integrity'] = get_integrity_hash( script.get( 'src' ) )
        new_script['crossorigin'] = 'anonymous'
        return_html = return_html.replace( old_script, str( new_script ) )

    return return_html

def get_integrity_hash( url ):
    if url in memoized_sha256_hashes:
        return memoized_sha256_hashes[ url ]
    if str( url ).startswith( '//' ):
        url = 'http:' + url
    if str( url ).startswith( '://' ):
        url = 'http' + url
    response = requests.get( url )
    hash_digest = hashlib.sha384( response.content ).digest()
    sig = 'sha384-' + base64.b64encode( hash_digest )
    memoized_sha256_hashes[ url ] = sig
    return sig

if len( sys.argv ) == 2:
    html_files = get_recursive_file_list( sys.argv[1], 'html' )
    html_files += get_recursive_file_list( sys.argv[1], 'htm' )

    for html_filename in html_files:
        new_html = get_sri_protected_html( get_soup_from_file( html_filename ) )
        file_handler = open( html_filename, 'w' )
        file_handler.write( new_html )
        file_handler.close()
else:
    print "No. Usage is " + sys.argv[0] + " /var/www/html/"
