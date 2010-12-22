from tornado.web import RequestHandler, HTTPError
from mako.template import Template
from mako.lookup import TemplateLookup
from tornado.options import options
from lib.session import Session
from lib.flash import Flash
import re, sys
from tornado import web
from urllib import unquote


class BaseRequest(RequestHandler):
    
    __template_exists_cache = {}
    
    def __init__(self, application, request, transforms=None):
        RequestHandler.__init__(self, application, request, transforms)
        self._current_user = None
        self.session = Session(self)
        self.flash = Flash()
    
    def template_exists(self, template_name):
        tmp = self.__template_exists_cache.get(template_name, None)
        if tmp != None:
            print "found in cache: " + template_name
            return tmp
        
        lookup = self._get_template_lookup()
        try:
            new_template = lookup.get_template(template_name)
            if new_template :
                self.__template_exists_cache[template_name] = True
                return True
        except Exception as detail:
            print 'run-time error in BaseRequest::template_exists - ', detail
        self.__template_exists_cache[template_name] = False   
        return False
        
        
    def _get_template_lookup(self) :
        return TemplateLookup(
            directories=[options.template_dir], 
            module_directory=options.mako_modules_dir, 
            output_encoding='utf-8', 
            encoding_errors='replace',
            imports=[
#                'from lib.trendrr.filters import Trendrr, Cycler',
            ]
        )
        
        
    
    def render_template(self,template_name, **kwargs):
        lookup = self._get_template_lookup()
        new_template = lookup.get_template(template_name)
           
        #add all the standard variables.
        kwargs['current_user'] = self.get_current_user()
        kwargs['render_as'] = self.get_argument('render_as', 'html')
        
        kwargs['is_logged_in'] = False
        if kwargs['current_user'] != None:
             kwargs['is_logged_in'] = True
        
        # allows us access to the request from within the template..
        kwargs['request'] = self.request
        
        kwargs['session'] = self.session
        
        #check if we have any flash messages set in the session
        if self.session.get('flash',False):     
            #add it to our template context args   
            kwargs['flash'] = self.session['flash']
            
            #remove the flash from the session
            del self.session['flash']
        else:
            #required in case we add flash without redirecting
            if len(self.flash):
                kwargs['flash'] = self.flash
        
        self.finish(new_template.render(**kwargs))

    '''
    hook into the end of the request
    '''
    def finish(self, chunk=None):
        if len(self.flash) > 0:
            self.session['flash'] = self.flash
        self.session.save()
        
        print "FINISH REQUEST!"
        super(BaseRequest, self).finish(chunk)
        del self.session
 
    '''
    hook into the begining of the request here
    '''
    def prepare(self):
        pass
            
    def get_current_user(self):
        return self._current_user
        
    def set_current_user(self, user):
        self._current_user = user        
    
    def is_logged_in(self):
        return self.get_current_user() != None
    
    '''
    gets all the request params as a map. cleans them all up ala get_argument(s)
    '''
    def get_arguments_as_dict(self):
        params = {}
        retVals = []
        for key in self.request.arguments:
            values = self.get_arguments(key)
            k = unquote(key)
            if len(values) == 1 :
                params[k] = values[0]
            else :
                params[k] = values
            
        return params
    
    '''
    Same as get_argument but will return a list 
    if no arguments are supplied then a dict of all
    the arguments is returned.
    '''
    def get_arguments(self, name=None,  default=None, strip=True):
        if name is None :
            return self.get_arguments_as_dict()
        
        values = self.request.arguments.get(name, None)
        if values is None:
            #if default is None:
            #    raise HTTPError(404, "Missing argument %s" % name)
            return default
        
        retVals = []
        for val in values :
            value = self._cleanup_param(val, strip)
            retVals.append(value)
        return retVals
    
    def get_argument(self, name, default=RequestHandler._ARG_DEFAULT, strip=True):
        value = super(BaseRequest, self).get_argument(name, default, strip)
        if value == default :
            return value
        return unquote(value)
    
    '''
        cleans up any argument
        removes control chars, unescapes, ect
    '''
    def _cleanup_param(self, val, strip=True):
        # Get rid of any weird control chars
        value = re.sub(r"[\x00-\x08\x0e-\x1f]", " ", val)
        value = web._unicode(value)
        if strip: value = value.strip()
        return unquote(value)   
    
    def get_username(self):
        if self.get_current_user() :
            return self.get_current_user()['_id']
        return None
        
    
    def write(self,chunk,status=None):
        if status:
            self.set_status(status)
        
        RequestHandler.write(self, chunk)
    
    def get_error_html(self, status_code, **kwargs): 
        print 'GOT ERROR: ', status_code
        
        if kwargs.has_key('exception'):
            print kwargs['exception']
        
        if status_code == 404 :
            self.redirect('/404')
        else : # call super.
            self.redirect('/error')
    
    
        