#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Citizen Cyberscience Centre
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import json
import datetime
import gdal
from gdalconst import *
from optparse import OptionParser

def frange(x, y, step):
    """Float Range Generator function"""
    while x < y:
        yield x
        x += step

def delete_app(api_url, api_key, id):
    """
    Deletes the application.

    :arg integer id: The ID of the application
    :returns: True if the application has been deleted
    :rtype: boolean
    """
    request = urllib2.Request(api_url + '/api/app/' + str(id) + '?api_key=' + api_key)
    request.get_method = lambda: 'DELETE'

    if (urllib2.urlopen(request).getcode() == 204): 
        return True
    else:
        return False

def update_app(api_url , api_key, id, name = None):
    """
    Updates the name of the application
    
    :arg integer id: The ID of the application
    :arg string name: The new name for the application
    :returns: True if the application has been updated
    :rtype: boolean
    """
    data = dict(id = id, name = name)
    data = json.dumps(data)
    request = urllib2.Request(api_url + '/api/app/' + str(id) + '?api_key=' + api_key)
    request.add_data(data)
    request.add_header('Content-type', 'application/json')
    request.get_method = lambda: 'PUT'

    if (urllib2.urlopen(request).getcode() == 200): 
        return True
    else:
        return False

def update_template(api_url, api_key, app='filtering'):
    """
    Update tasks template and long description for the application

    :arg string app: Application short_name in PyBossa.
    :returns: True when the template has been updated.
    :rtype: boolean
    """
    request = urllib2.Request('%s/api/app?short_name=%s' %
                              (api_url, app))
    request.add_header('Content-type', 'application/json')

    res = urllib2.urlopen(request).read()
    res = json.loads(res)
    res = res[0]
    if res.get('short_name'):
        # Re-read the template
        file = open('template.html')
        text = file.read()
        file.close()
        # Re-read the long_description
        file = open('long_description.html')
        long_desc = file.read()
        file.close()
        info = dict(thumbnail=res['info']['thumbnail'], task_presenter=text)
        data = dict(id=res['id'], name=res['name'],
                    short_name=res['short_name'],
                    description=res['description'], hidden=res['hidden'],
                    long_description=long_desc,
                    info=info)
        data = json.dumps(data)
        request = urllib2.Request(api_url + '/api/app/' + str(res['id']) + \
                                  '?api_key=' + api_key)
        request.add_data(data)
        request.add_header('Content-type', 'application/json')
        request.get_method = lambda: 'PUT'

        if (urllib2.urlopen(request).getcode() == 200):
            return True
        else:
            return False

    else:
        return False

def update_tasks(api_url, api_key, app='filtering'):
    """
    Update tasks question 

    :arg string app: Application short_name in PyBossa.
    :returns: True when the template has been updated.
    :rtype: boolean
    """
    request = urllib2.Request('%s/api/app?short_name=%s' %
                              (api_url, app))
    request.add_header('Content-type', 'application/json')

    res = urllib2.urlopen(request).read()
    res = json.loads(res)
    app = res[0]
    if app.get('short_name'):
        request = urllib2.Request('%s/api/task?app_id=%s&limit=%s' %
                                  (api_url, app['id'],'1000'))
        request.add_header('Content-type', 'application/json')

        res = urllib2.urlopen(request).read()
        tasks = json.loads(res)

        for t in tasks:
            t['info']['question']=u'Is this area too cloudy (more than 50% of the tile)?'
            data = dict(info=t['info'],app_id=t['app_id'])
            data = json.dumps(data)
            request = urllib2.Request(api_url + '/api/task/' + str(t['id']) + \
                                      '?api_key=' + api_key)
            request.add_data(data)
            request.add_header('Content-type', 'application/json')
            request.get_method = lambda: 'PUT'

            if (urllib2.urlopen(request).getcode() != 200):
                return False
            else:
                print "TASK %s updated" % (t['id'])

    else:
        return False

def create_app(api_url , api_key, name=None, short_name=None, description=None, template="template.html"):
    """
    Creates the application. 

    :arg string name: The application name.
    :arg string short_name: The slug application name.
    :arg string description: A short description of the application. 

    :returns: Application ID or 0 in case of error.
    :rtype: integer
    """
    print('Creating app')
    name = u'Filter cloudy areas' # Name with a typo
    short_name = u'filtering'
    description = u'Is this area too cloudy (more than 50% of the tile)?'
    # JSON Blob to present the tasks for this app to the users
    # First we read the template:
    file = open(template)
    text = file.read()
    file.close()
    info = dict (thumbnail="http://img36.imageshack.us/img36/285/cloudyr.jpg",
                 task_presenter = text)
    data = dict(name = name, short_name = short_name, description = description,
               hidden = 0, info = info)
    data = json.dumps(data)

    # Checking which apps have been already registered in the DB
    apps = json.loads(urllib2.urlopen(api_url + '/api/app' + '?api_key=' + api_key).read())
    for app in apps:
        if app['short_name'] == short_name: 
            print('{app_name} app is already registered in the DB'.format(app_name = name))
            print('Deleting it!')
            if (delete_app(api_url, api_key, app['id'])): print "Application deleted!"
    print("The application is not registered in PyBOSSA. Creating it...")
    # Setting the POST action
    request = urllib2.Request(api_url + '/api/app?api_key=' + api_key )
    request.add_data(data)
    request.add_header('Content-type', 'application/json')

    # Create the app in PyBOSSA
    output = json.loads(urllib2.urlopen(request).read())
    if (output['id'] != None):
        print("Done!")
        return output['id']
    else:
        print("Error creating the application")
        return 0

def create_task(api_url , api_key, app_id, tile):
    """
    Creates tasks for the application

    :arg integer app_id: Application ID in PyBossa.
    :returns: Task ID in PyBossa.
    :rtype: integer
    """
    # Process the tile
    dataset = gdal.Open(tile, GA_ReadOnly)
    print 'Driver: %s' % dataset.GetDriver().ShortName
    print 'Size is %s x %s y' % (dataset.RasterXSize, dataset.RasterYSize)
    width  = dataset.RasterXSize
    height = dataset.RasterYSize
    print 'Projection is: %s' % dataset.GetProjection()

    # From http://osgeo-org.1560.n6.nabble.com/get-corner-coordinates-from-gdalopen-td3749527.html
    gt = dataset.GetGeoTransform()
    minX = gt[0]
    minY = gt[3] + width*gt[4] + height*gt[5]
    maxX = gt[0] + width*gt[1] + height*gt[2]
    maxY = gt[3]
    bounds = [minX, minY, maxX, maxY]
    print 'Bounds: %s' % bounds

    # Compute the restrictedExtents for the tiles:
    numTiles =  16
    x = 0
    y = 0
    stepX = ((maxX - minX)/numTiles)
    stepY = ((maxY - minY)/numTiles)
    extents = []
    for x in frange(minX, maxX, stepX ):
        for y in frange(minY, maxY, stepY):
            extents.append([x,y, x + stepX, y + stepY])

    # Create a task per extent
    for e in extents:
        # Data for the tasks
        t    = dict (name = tile.rstrip(),
                     bounds = bounds,
                     restrictedExtent = e,
                     projection = dataset.GetProjection(),
                     width = width,
                     height = height
                )
        info = dict (tile=t, question=u'Is this area too cloudy (more than 50% of the tile)?')
        data = dict (app_id = app_id, state = 0, info = info, calibration = 0, priority_0 = 0)
        data = json.dumps(data)

        # Setting the POST action
        request = urllib2.Request(api_url + '/api/task' + '?api_key=' + api_key)
        request.add_data(data)
        request.add_header('Content-type', 'application/json')

        # Create the task
        output = json.loads(urllib2.urlopen(request).read())
        if (output['id'] == None):
            return False

def get_tiles(file):
    """
    Gets tiles from a file 
    
    :arg string file: File name that has all the tiles names
    :returns: A list of tiles.
    :rtype: list
    """
    file = open(file)
    tiles = file.readlines()
    file.close()
    return tiles 


import sys
if __name__ == "__main__":
    # Arguments for the application
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    
    parser.add_option("-s", "--server", dest="api_url", help="PyBossa URL http://domain.com/", metavar="URL")
    parser.add_option("-k", "--api-key", dest="api_key", help="PyBossa User API-KEY to interact with PyBossa", metavar="API-KEY")
    parser.add_option("-p", "--template", dest="template", help="PyBossa HTML+JS template for application presenter", metavar="TEMPLATE")
    parser.add_option("-t", "--tiles", dest="tiles", help="File with the name of the tiles", metavar="TILES")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    # Create App
    parser.add_option("-a", "--create-app", action="store_true",
                      dest="create_app",
                      help="Create the application",
                      metavar="CREATE-APP")


    # Update template for tasks and long_description for app
    parser.add_option("-u", "--update-template", action="store_true",
                      dest="update_template",
                      help="Update Tasks template",
                      metavar="UPDATE-TEMPLATE"
                     )
    # Update tasks question
    parser.add_option("-q", "--update-tasks", action="store_true",
                      dest="update_tasks",
                      help="Update Tasks question",
                      metavar="UPDATE-TASKS"
                     )

    
    (options, args) = parser.parse_args()

    if not options.api_url:
        options.api_url = 'http://localhost:5000'

    if not options.api_key:
        parser.error("You must supply an API-KEY to create an applicationa and tasks in PyBossa")

    if not options.template:
        print("Using default template: template.html")
        options.template = "template.html"

    if not options.tiles:
        parser.error("You must supply a file name with the tiles")

    if (options.verbose):
       print('Running against PyBosssa instance at: %s' % options.api_url)
       print('Using API-KEY: %s' % options.api_key)

    if options.update_template:
        print "Updating app template"
        update_template(options.api_url, options.api_key)

    if options.update_tasks:
        print "Updating task question"
        update_tasks(options.api_url, options.api_key)

    if options.create_app:
        app_id = create_app(options.api_url, options.api_key, template = options.template)
        tiles = get_tiles(options.tiles)
        #for tile in tiles:
            #create_task(options.api_url, options.api_key, app_id, tile)
        create_task(options.api_url, options.api_key, app_id, 'demo.tif')
    if not options.create_app and not options.update_template:
        parser.error("Please check --help or -h for the available options")
