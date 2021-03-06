#!/usr/bin/env python
#
#    Authtor: James Percent (james@empty-set.net)
#    Copyright 2010, 2011 James Percent
# 
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import re
import sys
import logging

import ply.lex as lex
import ply.yacc as yacc

logger = logging.getLogger(__name__)
def set_logger_level(logLevel):
    logger.setLevel(logLevel)

class Bundle:
    def __init__(self):
        # Sym_name is the name of bundle; version is the bundle's version and it
        # gets appended to the end of the jar file; root is the os path to the
        # src or jar file; jar indicates whether or not the bundle is a jar
        # library or a source bundle; deps is a tree of dependent bundles (of
        # type Bundle); extra_libs are a list of none OSGi jar files that are
        # included; classpath is the transitively closed classpath of bundles;
        # build level is the order in which the source bundles need to be built.
        self.id = ''
        self.sym_name = ''
        self.ipackages = []
        self.epackages = []
        self.rbundles = []
        self.junit_tests = []
        self.version = Version()
        self.root = ''
        self.is_binary_bundle = False
        self.file = ''
        self.fragment = False
        self.fragment_host = None
        self.deps = {}
        self.build_level = 0
        self.classpath = None
        self.extra_libs = {}
        self.binary_bundle_dir = False
        self.classpath_jars = []
    
    def load_from_database(self, result):
        assert len(result) == 12
        self.id = result[0]
        self.sym_name = result[1]
        self.version.set_major(result[2])
        self.version.set_minor(result[3])
        self.version.set_micro(result[4])
        self.version.set_qual(result[5])
        self.root = result[6]
        self.is_binary_bundle = result[7]
        self.file = result[8]
        self.fragment = result[9]
        self.fragment_host = result[10]
        self.binary_bundle_dir = result[11]
        
    def add_ipackage(self, i):
        self.ipackages.append(i)
       
    def add_epackage(self, e):
        self.epackages.append(e)
        
    # Note, that the parameter is a Package, which is sufficient "lookup info."
    def add_required_bundle_lookup_info(self, b):
        self.rbundles.append(b)
        
    def add_dep(self, bundle):
        self.deps[bundle] = bundle
       
    def display(self):
        print        'Symbolic Name     = ',self.sym_name
        if self.is_binary_bundle == True:
            print    'Java Archive      = ', os.path.join(self.root, self.file)
        else:
            print    'Source Directory  = ', self.root
        imports =    'Imported Packages = '
        exports =    'Exported Packages = '
        rbundles =   'Required Bundles  = '
        wrap_start = '                    '
            
        for i in  self.ipackages:
            for c in i.name:
                if ((len(imports) + 1) % 80) == 0:
                    imports += '\n'+wrap_start + c
                else:
                    imports += c
            if ((len(imports) + 1) % 80) == 0:
                imports += '\n'+wrap_start
            else:
                imports += ','
        print imports[:len(imports) - 1]                
          
        for e in  self.epackages:
            for c in e.name:
                if ((len(exports) + 1) % 80) == 0:
                    exports += '\n'+wrap_start + c
                else:
                    exports += c
            if ((len(exports) + 1) % 80) == 0:
                exports += '\n'+wrap_start
            else:
                exports += ','            
        print exports[:len(exports) - 1]
           
        for i in  self.rbundles:
            for c in i.name:
                if ((len(rbundles) + 1) % 80) == 0:
                    rbundles += '\n'+wrap_start + c
                else:
                    rbundles += c
            if ((len(rbundles) + 1) % 80) == 0:
                rbundles += '\n'+wrap_start
            else:
                rbundles += ','
        print rbundles[:len(rbundles) - 1]                
        
class Package:
    def __init__(self, name):
        self.name = name
        self.b_version = Version()
        self.e_version = Version()
        self.e_version.set_major(str(sys.maxint))
        self.b_inclusive = True
        self.e_inclusive = True
     
    def __str__(self):
        string = ''
        assert self.b_version != None and self.e_version != None
            
        if self.b_inclusive:
            string += '['
        else:
            string += '('
            
        string += self.b_version.__str__() +','+ self.e_version.__str__()
          
        if self.e_inclusive:
            string += ']'
        else:
            string += ')'
            
        return string
       
    def set_version_range(self, bversion, b_inc, eversion, e_inc):
        assert isinstance(bversion, Version) and isinstance(eversion, Version)
        self.b_version = bversion
        self.b_inclusive = b_inc
        self.e_version = eversion
        self.e_inclusive = e_inc
            
    def is_in_range(self, version):
        if version.is_less(self.b_version) or (version.is_equal(self.b_version) \
            and self.b_inclusive):
            if self.e_version.is_less(version) or (self.e_inclusive and \
                self.e_version.is_equal(version)):
                    return True
            else:
                return False
        else:
            return False
            
class Version:
    def __init__(self):
        self.major = '0'
        self.major_set = False
        self.minor = '0'
        self.minor_set = False
        self.micro = '0'
        self.micro_set = False        
        self.qual = '0'
        self.qual_set = False        
        
    def __str__(self):
        string = ''
        if(self.major_set):
            string += str(self.major)
        else:
            return string
           
        if(self.minor_set):
            string = string + '.' +str(self.minor)
        else:
            return string
           
        if(self.micro_set):
            string = string + '.' +str(self.micro)
        else:
            return string
        
        if(self.qual_set):
            string = string + '.' +str(self.qual)
            
        return string        
           
    def set_major(self, major):
        self.major_set = True
        self.major = str(major)
            
    def set_minor(self, minor):
        self.minor_set = True
        self.minor = str(minor)
            
    def set_micro(self, micro):
        self.micro_set = True
        self.micro = str(micro)
            
    def set_qual(self, qual):
        self.qual_set = True
        self.qual = str(qual)
            
    def is_less(self, version):
        if int(self.major) < int(version.major):
            return False
        elif int(self.major) > int(version.major):
            return True
        elif int(self.minor) < int(version.minor):
            return False
        elif int(self.minor) > int(version.minor):
            return True
        elif int(self.micro) < int(version.micro):
            return False
        elif int(self.micro) > int(version.micro):
            return True
        elif self.qual < version.qual:
            return False
        elif self.qual > version.qual:
            return True
        else:
            # must be equal
            return False
            
    def is_equal(self, version):
        if self.major == version.major and self.minor == version.minor and \
           self.micro == version.micro and self.qual == version.qual:
            return True
        else:
            return False
            
          
class Ast:
    def __init__(self):
        self.bundle = Bundle()
            
    def bundle_symbolic_name(self, p):
        logger.debug(' bundle symbolic name ')
        assert len(p) == 3 or len(p) == 4
        if len(p) == 3:
            self.bundle.sym_name = p[2]
            #self.bundle.sym_name        
        
    def bundle_version(self, p):
        assert len(p) == 3
        if isinstance(p[2], Version): 
            self.bundle.version = p[2]
        else:
            self.bundle.version = Version()

    def fragment_host(self,p):
        assert len(p) == 3 or len(p) == 5
        # another h4x0r
        self.bundle.fragment = True
        self.bundle.fragment_host = Package(p[2])
        if len(p) == 5:
            self.bundle.fragment_host.set_version_range(p[4][0], p[4][1], p[4][2], p[4][3])
        self.bundle.add_required_bundle_lookup_info(self.bundle.fragment_host)
        
    def packages(self, p):
        logger.debug(' packages ')
        logger.debug(p[0], p[1], p[2])
        assert len(p) == 3 and p[2] != None
        
        packages = p[2]
        cmd = p[1]
        
        for i in packages:            
            if cmd == 'Import-Package:':
                self.bundle.add_ipackage(i)
                logger.debug('---- adding import package ----'+str(i))
            elif cmd == 'Export-Package:':
                if i.name == 'javax.xml.namespace':
                    assert False
                self.bundle.add_epackage(i)
                logger.debug('---- adding export package ----'+str(i))                        
            elif cmd == 'Require-Bundle:':
                # h4x0r
                self.bundle.add_required_bundle_lookup_info(i)
            else:
                assert False
                
    def requires(self, p):
        logger.debug(' requires ')
        assert len(p) == 2 or len(p) == 4
        if len(p) == 2:
            p[0] = p[1]
        else:
            logger.debug(p[1], p[2], p[3])
            assert p[1] != None
            p[1].extend(p[3])
            p[0] = p[1]
            
    def require(self, p):
        logger.debug(' require ')
        assert len(p) == 2 or len(p) == 4
        if len(p) == 2:
            p[0] = p[1]
        else:
            assert len(p[1]) == 1 or p[3] == None
            if p[3] != None:
                assert len(p[3]) == 4
                logger.debug(str(p[1]) + ' '+ str(p[3]))
                p[1][0].set_version_range(p[3][0], p[3][1], p[3][2], p[3][3])
            p[0] = p[1]
               
    def package_names(self, p):
        logger.debug(' package-names ')
        if len(p) == 2:
            p[0] = [Package(p[1]),]
        else:
            assert len(p) == 4
            p[0] = p[1].append(Package(p[3]))
            
    def package_name(self, p):
        logger.debug('package_name')
        if len(p) == 4:
            p[0] = p[1]+p[2]+p[3]
        elif len(p) == 3:
            p[0] = p[1]+p[2]
        else:
            assert len(p) == 2
            p[0] = p[1]
    def parameter(self, p):
        logger.debug('parameter '+str(p[1])+str(len(p)))
        assert len(p) == 2 or len(p) == 4
        assert p[0] == None or p[3] == None
        # XXX - this is a hack
        if p[1] != None:
            p[0] = p[1]
        elif len(p) == 4 and p[3] != None:
            p[0] = p[3]
        logger.debug('----------------'+str(p[0]))
        
    def version(self, p):
        #logger.debug(' version ')
        assert len(p) == 4
        p[0] = p[3]
        
    def version_string(self, p):
        assert len(p) == 2 or len(p) == 4 or len(p) == 8
        #print' version string', p[0], p[1], p[2], p[3]
        if len(p) == 2 or len(p) == 4:
            v = Version()
            v.set_major(str(sys.maxint))
        
        if len(p) == 2:
            p[0] = [p[1], True, v, False]
        elif len(p) == 4:
            p[0] = [p[2], True, v, False]
        elif len(p) == 8 and p[2] == '(' and p[6] == ')':
            p[0] = [p[3], False, p[5], False]
        elif len(p) == 8 and p[2] == '(' and p[6] == ']':
            p[0] = [p[3], False, p[5], True]
        elif len(p) == 8 and p[2] == '[' and p[6] == ')':
            p[0] = [p[3], True, p[5], False]
        elif len(p) == 8 and p[2] == '[' and p[6] == ']':
            p[0] = [p[3], True, p[5], True]            
        else:
            #print p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], len(p)
            assert False
        
    def version_number(self, p):
        assert len(p) <= 8
        #print ' version number '
        if p[1] != 'version_number':
            p[0] = Version()
        else:
            #print p[1]
            assert False
            
        if len(p) >= 2:
            p[0].set_major(p[1])
        if len(p) >= 4:
            p[0].set_minor(p[3])
        if len(p) >= 6:
            p[0].set_micro(p[5])
        if len(p) == 8:
            p[0].set_qual(p[7])
        
        
    def directive(self, p):
        pass
        
class ManifestParser:    
    precedence = ()
    reserved = {
        'Import-Package:' : 'IMPORT_PACKAGE',
        'Export-Package:' : 'EXPORT_PACKAGE',
        'Bundle-SymbolicName:': 'BUNDLE_SYMBOLIC_NAME',
        'Bundle-Version:' : 'BUNDLE_VERSION',
        'Bundle-Name:' : 'BUNDLE_NAME',
        'Require-Bundle:' : 'REQUIRE_BUNDLE',
        'Fragment-Host:' : 'FRAGMENT_HOST'
    }
        
    tokens = ('DOT','COLON', 'COMMA', 'SEMI_COLON', 'QUOTE', 'LPAREN', 'RPAREN',
              'RANGLE', 'LANGLE', 'NUMBER', 'HEADER', 'ID', 'TOKEN',
              'SLASH', 'EQUAL', 'PERCENT', 'PLUS', 'DOLLAR')+ tuple(reserved.values())
    
    t_COLON = r'\:'
    t_COMMA = r'\,'
    t_DOT = r'\.'
    t_SEMI_COLON = r'\;'
    t_EQUAL = r'='
    t_LANGLE = r'\['
    t_RANGLE = r'\]'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_SLASH = r'\/'
    t_QUOTE = r'\"'
    t_PERCENT = r'%'
    t_PLUS = r'\+'
    t_DOLLAR = '\$'
    t_ignore = " \t"
    
    def __init__(self, **kw):
        #self.debug = kw.get('debug', 0)
        self.names = { }
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[1] + \
            "_" + self.__class__.__name__
        except:
            modname = "parser"+"_"+self.__class__.__name__
        #self.debugfile = modname + ".dbg"
        #self.tabmodule = modname + "_" + "parsetab"
        #print self.debugfile, self.tabmodule

        lex.lex(module=self)#, debug=self.debug)
        
        yacc.yacc(module=self, method="SLR")#,
                  #debug=self.debug,
                  #debugfile=self.debugfile,
                  #tabmodule=self.tabmodule)    
        
    def t_error(self, t):
        #print 'Illegal character t.value[0] --->',t,'<----'
        t.lexer.skip(1)
            
    def t_NUMBER(self, t):
        r'[0-9]+'
        #print 't_NUMBER'
        return t
    
    def t_HEADER(self, t):
        r'^[a-zA-Z_0-9]*\-[a-zA-Z_][a-zA-Z_0-9]*\:'
        t.type = ManifestParser.reserved.get(t.value, 'HEADER')
        #print 't_HEADER ', t.value, t.type
        return t    

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9\$]*'    
        t.type = ManifestParser.reserved.get(t.value, 'ID')
        #print 't_ID', t.value, t.type
        return t
            
    def t_TOKEN(self, t):
        r'[a-zA-Z0-9_-][a-zA-Z0-9-_\$\+\=]*'
        t.type = ManifestParser.reserved.get(t.value, 'TOKEN')
        #print 't_TOKEN ', t.value, t.type
        return t
            
    def p_header(self, p):
        '''header : packages
                 | bundle_symbolic_name
                 | bundle_version
                 | bundle_name
                 | fragment_host'''
        pass

#    def p_bundle_classpath(self, p):
#        '''bundle_classpath : BUNDLE_CLASSPATH TOKEN DOT ID
#                  | BUNDLE_CLASSPATH ID DOT ID'''
#        self.ast.bundle_classpath(p)

    def p_fragment_host(self, p):
        '''fragment_host : FRAGMENT_HOST package_name
                        | FRAGMENT_HOST package_name SEMI_COLON parameter'''
        self.ast.fragment_host(p)
            
    def p_bundle_version(self, p):
        '''bundle_version : BUNDLE_VERSION version_number
                        | BUNDLE_VERSION ID'''
        self.ast.bundle_version(p)
        
    def p_bundle_name(self, p):
        '''bundle_name : BUNDLE_NAME'''
        assert False

    def p_bundle_symbolic_name(self, p):
        '''bundle_symbolic_name : BUNDLE_SYMBOLIC_NAME package_name
                                |  bundle_symbolic_name SEMI_COLON parameter'''
        self.ast.bundle_symbolic_name(p)
    #    
    #def p_jdk_version(self, p):
    #    '''jdk_version : TOKEN
    #           | ID
    #           | jdk_version DOT
    #           | jdk_version ID
    #           | jdk_version TOKEN
    #           | jdk_version COMMA
    #           | jdk_version NUMBER
    #           | jdk_version SLASH'''
    #    self.ast.jdk_version(p)
    #    
    #def p_url(self, p):
    #    '''url : ID COLON SLASH SLASH
    #        | url ID
    #        | url TOKEN
    #        | url DOT ID
    #        | url DOT TOKEN
    #        | url SLASH ID
    #        | url SLASH TOKEN'''
    #    self.ast.url(p)
    #    
    
    def p_packages(self, p):
        '''packages : IMPORT_PACKAGE requires
                    | EXPORT_PACKAGE requires
                    | REQUIRE_BUNDLE requires'''
        self.ast.packages(p)
            
    def p_requires(self, p):
        '''requires : require
                    | requires COMMA require'''
        self.ast.requires(p)
            
    def p_require(self, p):
        '''require : package_names
                   | package_names SEMI_COLON parameter'''
        self.ast.require(p)
            
    def p_package_names(self, p):
        '''package_names : package_name
                         | package_names SEMI_COLON package_name'''
#                         | package_names SEMI_COLON parameter'''
        self.ast.package_names(p)
            
    def p_package_name(self, p):
        '''package_name : ID
                        | package_name DOT ID
                        | package_name TOKEN
                        | package_name ID
                        | package_name DOT NUMBER'''
        self.ast.package_name(p)

    def p_parameter(self, p):
        '''parameter : version
                     | directive
                     | parameter SEMI_COLON version
                     | parameter SEMI_COLON directive'''
        self.ast.parameter(p)
            
    def p_directive(self, p):
        '''directive : TOKEN COLON EQUAL TOKEN
                     | ID EQUAL QUOTE ID QUOTE
                     | TOKEN COLON EQUAL ID
                     | ID COLON EQUAL TOKEN
                     | ID COLON EQUAL ID
                     | ID COLON EQUAL QUOTE unused_package_name QUOTE
                     | ID TOKEN COLON EQUAL QUOTE unused_package_name QUOTE
                     | ID TOKEN COLON EQUAL ID'''
        #print 'directive'
        self.ast.directive(p)

    def p_unused_package_name(self, p):
        '''unused_package_name : package_name
                               | unused_package_name COMMA package_name'''
        #print 'unused package name'
        
    def p_version(self, p):
        '''version : TOKEN EQUAL version_string
                    | ID EQUAL version_string
                    | ID TOKEN EQUAL version_string'''
#                   | ID EQUAL version_number ''' # hack for bundle-version
        self.ast.version(p)
            
    def p_version_string(self, p):

        '''version_string : QUOTE version_number QUOTE
                         | version_number
                          | QUOTE LPAREN version_number COMMA version_number RPAREN QUOTE
                          | QUOTE LPAREN version_number COMMA version_number RANGLE QUOTE
                          | QUOTE LANGLE version_number COMMA version_number RANGLE QUOTE
                          | QUOTE LANGLE version_number COMMA version_number RPAREN QUOTE'''
        self.ast.version_string(p)
            
    def p_version_number(self, p):
        '''version_number : NUMBER
                          | NUMBER DOT NUMBER
                          | NUMBER DOT NUMBER DOT NUMBER
                          | NUMBER DOT NUMBER DOT NUMBER DOT NUMBER
                          | NUMBER DOT NUMBER DOT NUMBER DOT ID
                          | NUMBER DOT NUMBER DOT NUMBER DOT TOKEN
                          | version_number DOT ID
                          | version_number DOT TOKEN
                          | version_number ID
                          | version_number TOKEN'''
        self.ast.version_number(p)
            
    def p_error(self, p):
        if p:
            print "Syntax error at '%s'" % p.value
        else:
            print "Syntax error at EOF"
        raise SyntaxError
    
    def parse(self, manifest):
        assert manifest != None
        # remove \r if it's there...
        manifest = re.sub(r'\r','',  manifest)
        #concat multi line headers, which makes parsing simplier
        manifest = re.sub(r'\n ', '', manifest)
        headers = re.split(r'\n', manifest)

        self.ast = Ast() 
        parsed = False
        
        for header in headers:
            if header.startswith('Import-Package:') \
                or header.startswith('Export-Package:') \
                or header.startswith('Require-Bundle:') \
                or header.startswith('Bundle-SymbolicName:') \
                or header.startswith('Fragment-Host:') \
                or header.startswith('Bundle-ClassPath:') \
                or header.startswith('Bundle-Version:'):
                
                # h4x0r
                if header.startswith('Bundle-ClassPath:'):
                    firstSplit = header.split(':')[1:]
#                    print firstSplit
                    assert firstSplit.__len__() == 1
                    classPathValues = firstSplit[0].split(',')
                    
                    for index in range(0, classPathValues.__len__()):
                        classPathValues[index] = \
                          classPathValues[index].replace(' ', '')
                        #print classPathValues[index], classPathValues[index].endswith('.jar')                         
                        if not classPathValues[index].endswith('.jar'):
                            if len(classPathValues) == 1:
                                continue
                            else:
                                classPathValues.remove(classPathValues[index])
                            
                    self.ast.bundle.classpath_jars = classPathValues
                    continue
                    
                # h4x0r                    
                if header.startswith('Require-Bundle:') \
                    or header.startswith('Fragment-Host:'):
                    header = re.sub(r'bundle-', '', header)
                
                yacc.parse(header)
                parsed = True
        
        if parsed:
            return self.ast.bundle
        else:
            return None
        
