# -*- coding: utf-8 -*-

from unittest import TestCase
import RDF
import logging
import sys
import utils

logging.basicConfig(
    level=logging.INFO, format='%(message)s', stream=sys.stdout)

class UtilsTestCase(TestCase):
    def setUp(self):
        self.model = RDF.Model(utils.open_triplestore())
    def test_normalize_topic_name(self):
        def test(name, normalized):
            self.assertEquals(
                utils.normalize_topic_name(name), normalized)
        test(u'Lanval, Marc, 1898?-1955?',
             u'Marc Lanval')
        test(u'Maximoff, G. P.(Gregori Petrovich), 1893-1950',
             u'G. P. Maximoff')
        test(u'Abad de Santillán, Diego',
             u'Diego Abad de Santillán')
        test(u'Abbott, Leonard Dalton, 1878-1953',
             u'Leonard Dalton Abbott')
        test(u'Abrams, Irving S., 1891-1980',
             u'Irving S. Abrams')
        test(u'Andrews, Esther B. Hussey 1871',
             u'Esther B. Hussey Andrews')
        test(u'Andreytchine, George E., c.1894-1949?',
             u'George E. Andreytchine')
        test(u'Antolini, Gabriella (Ella) (1899-1984)',
             u'Gabriella Antolini')
        test(u'Baginski, Emilie “Millie” (née Schumm) (d. unknown)',
             u'Emilie "Millie" Baginski')
        test(u'Baron, Rose (no dates)',
             u'Rose Baron')
        test(u'Bauer, Augustin Souchy, 1892-',
             u'Augustin Souchy Bauer')
        test(u'Beck, Kathryn, “Kitty” (?-1924).',
             u'Kathryn Beck')
        test(u'Bernstein, Ethel (b. 1898)',
             u'Ethel Bernstein')
        test(u'Bernstein, Rose (Mirsky) (dates unknown)',
             u'Rose Bernstein')
        test(u'George, Harrison, 1888-19??',
             u'Harrison George')
        test(u'Fitzgerald, Margaret Eleanor (“Fitzie”) (1877-1955)',
             u'Margaret Eleanor Fitzgerald')
        test(u'Anarchist Exclusion Act 1918',
             u'Anarchist Exclusion Act')
        test(u'Anarchist Soviet Bulletin, The',
             u'The Anarchist Soviet Bulletin')
        test(u'India, eugenics in',
             u'eugenics in India')
        test(u'Kennan, Ellen A., (c. 1873-c.1950)',
             u'Ellen A. Kennan')
    def test_encode_uri(self):
        self.assertRaises(Exception, utils.encode_uri, 
                          'http://dbpedia.org/resource/foo')
        self.assertEquals(
            utils.encode_uri(u'http://berkeley.edu/'),
            'http://berkeley.edu/')
        self.assertEquals(
            utils.encode_uri(
                u'http://dbpedia.org/resource/Diego_Abad_de_Santillán'),
            'http://dbpedia.org/resource/Diego_Abad_de_Santill%C3%A1n')
        self.assertEquals(
            utils.encode_uri(
                u'http://th.is/url has spaces/'),
            'http://th.is/url%20has%20spaces/')
    def test_find_possible_uris(self):
        # single LATIN SMALL LETTER E WITH ACUTE
        variant1 = u'Abad de Santill\u00e1n, Diego'
        sets = utils.find_possible_uris(variant1)
        self.assertEquals(len(sets), 8)
        self.assertEquals(len(sets[0]), 6)
        self.assertEquals(
            sets[0][0], 
            'http://dbpedia.org/resource/Abad_de_Santill%C3%A1n')
        # lower-case a with COMBINING ACUTE ACCENT
        variant2 = u'Abad de Santilla\u0301n, Diego'
        sets = utils.find_possible_uris(variant2)
        self.assertEquals(len(sets), 8)
        self.assertEquals(len(sets[0]), 6)
        self.assertEquals(
            sets[0][0], 
            'http://dbpedia.org/resource/Abad_de_Santill%C3%A1n')
    def test_find_best_uris(self):
        uri_set = utils.find_best_uris(self.model, u'Abad de Santillán, Diego')
        self.assertEquals(len(uri_set), 5)
        self.assertTrue(
            'http://rdf.freebase.com/ns/guid.9202a8c04000641f8000000000319690'
            in uri_set)
    def test_find_dbpedia_labels(self):
        self.assertRaises(
            Exception, utils.find_dbpedia_labels,
            u'http://dbpedia.org/resource/Diego_Abad_de_Santillán')
        labels = utils.find_dbpedia_labels(
            'http://dbpedia.org/resource/Diego_Abad_de_Santill%C3%A1n')
        self.assertEquals(
            labels,
            [(u'Diego Abad de Santillán','en'),
             (u'Diego Abad de Santillán','es'),
             (u'Diego Abad de Santillán','pt')])
    def test_find_labels(self):
        labels = utils.find_labels(
            'http://dbpedia.org/resource/Diego_Abad_de_Santill%C3%A1n')
        self.assertEquals(
            labels,
            [(u'Diego Abad de Santillán','en'),
             (u'Diego Abad de Santillán','es'),
             (u'Diego Abad de Santillán','pt')])
        labels = utils.find_labels('http://rdf.freebase.com/ns/m.05ynyn')
        self.assertEquals(
            labels,
            [(u'Hippolyte Havel','en')])
        labels = utils.find_labels('http://rdf.freebase.com/ns/m/072wkb')
        self.assertEquals(
            labels,
            [(u'Rose Pastor Stokes','en')])
        labels = utils.find_labels('http://purl.org/dc/terms/subject')
        self.assertEquals(
            labels,
            [(u'Subject','en-us')])
    def test_get_cached_labels(self):
        uri = 'http://th.is/dont/exist'
        labels = utils.get_cached_labels(self.model, uri)
        self.assertEquals(labels, [])
        utils.add_label(self.model, uri, 'this does not exist')
        labels = utils.get_cached_labels(self.model, uri)
        self.assertEquals(labels, [('this does not exist', 'en')])
    def test_get_cached_label(self):
        uri = 'http://th.is/dont/exist/either'
        label = utils.get_cached_label(self.model, uri)
        self.assertEquals(label, None)
        utils.add_label(self.model, uri, 'this does not exist')
        label = utils.get_cached_label(self.model, uri)
        self.assertEquals(label, 'this does not exist')
        label = utils.get_cached_label(self.model, uri, lang='en')
        self.assertEquals(label, 'this does not exist')
        label = utils.get_cached_label(self.model, uri, lang='fr')
        self.assertEquals(label, None)
        utils.add_label(self.model, uri, "cela n'existe pas", 'fr')
        label = utils.get_cached_label(self.model, uri, lang='fr')
        self.assertEquals(label, "cela n'existe pas")
    def test_get_source_context_node(self):
        self.assertEquals(
            utils.get_source_context_node(
                'http://dbpedia.org/resource/Diego_Abad_de_Santill%C3%A1n'),
            RDF.Node(RDF.Uri('http://dbpedia.org/')))
        self.assertEquals(
            utils.get_source_context_node(
                'http://rdf.freebase.com/ns/m.05ynyn'),
            RDF.Node(RDF.Uri('http://rdf.freebase.com/')))
    def test_check_object_literal_language(self):
        self.assertEquals(
            utils.check_object_literal_language(
                utils.label_statement('http://foobar.com/', 'FooBar')),
            RDF.Statement(
                RDF.Uri('http://foobar.com/'), 
                utils.rdfs.label, 
                RDF.Node(literal='FooBar', language='en')))
        self.assertEquals(
            utils.check_object_literal_language(
                utils.label_statement('http://foobar.com/', 'Le FooBar', 'fr')),
            RDF.Statement(
                RDF.Uri('http://foobar.com/'), 
                utils.rdfs.label, 
                RDF.Node(literal='Le FooBar', language='fr')))
    def test_load_triples(self):
        def reject(statement):
            if statement.object.is_literal():
                return (not statement.object.literal[1].startswith('en'))
            return False
        candidates = RDF.Node(RDF.Uri('http://editorsnotes.org/test/'))
        source = RDF.Node(RDF.Uri('http://editorsnotes.org/test/source/'))
        uri = 'http://dbpedia.org/resource/Diego_Abad_de_Santill%C3%A1n'
        count, predicate_uris, object_uris = utils.load_triples(
            self.model, candidates, uri, reject=reject, source=source)
        self.assertEquals(count, 37)
        self.assertEquals(len(predicate_uris), 12)
        self.assertTrue(
            RDF.Uri('http://dbpedia.org/ontology/abstract') in predicate_uris)
        self.assertEquals(len(object_uris), 34)
        self.assertTrue(
            RDF.Uri('http://ludd.net/~adamw/malatesta/') in object_uris)
        self.assertEquals(
            utils.count_all_statements(self.model, candidates), 37)
        self.assertEquals(
            utils.count_all_statements(self.model, source), 55)
    def tearDown(self):
        for uri in ['http://th.is/dont/exist',
                    'http://th.is/dont/exist/either']:
            utils.remove_cached_labels(self.model, uri)
        utils.remove_statements_with_context(
            self.model, 'http://editorsnotes.org/test/')
        utils.remove_statements_with_context(
            self.model, 'http://editorsnotes.org/test/source/')
    
        
        
        
