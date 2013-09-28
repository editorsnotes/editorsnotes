EditorsNotes.CSL.JSONFormats = {}
EditorsNotes.CSL.JSONFormats['chicago-fullnote-bibliography'] = {
  "children": [
    {
      "children": [
        {
          "children": [], 
          "name": "title", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "id", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "link", 
          "attrs": {
            "href": "http://www.zotero.org/styles/chicago-fullnote-bibliography"
          }
        }, 
        {
          "children": [], 
          "name": "link", 
          "attrs": {
            "href": "http://www.chicagomanualofstyle.org/tools_citationguide.html", 
            "rel": "documentation"
          }
        }, 
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {}
            }, 
            {
              "children": [], 
              "name": "email", 
              "attrs": {}
            }
          ], 
          "name": "author", 
          "attrs": {}
        }, 
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {}
            }, 
            {
              "children": [], 
              "name": "email", 
              "attrs": {}
            }
          ], 
          "name": "contributor", 
          "attrs": {}
        }, 
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {}
            }, 
            {
              "children": [], 
              "name": "email", 
              "attrs": {}
            }
          ], 
          "name": "contributor", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "summary", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "category", 
          "attrs": {
            "term": "generic-base"
          }
        }, 
        {
          "children": [], 
          "name": "category", 
          "attrs": {
            "term": "numeric"
          }
        }, 
        {
          "children": [], 
          "name": "updated", 
          "attrs": {}
        }
      ], 
      "name": "info", 
      "attrs": {}
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "label", 
                          "attrs": {
                            "suffix": ". ", 
                            "form": "verb-short", 
                            "text-case": "lowercase"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "name", 
                          "attrs": {
                            "and": "text", 
                            "delimiter": ", "
                          }
                        }
                      ], 
                      "name": "names", 
                      "attrs": {
                        "variable": "editor", 
                        "delimiter": ", "
                      }
                    }
                  ], 
                  "name": "if", 
                  "attrs": {
                    "variable": "author"
                  }
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "label", 
                          "attrs": {
                            "suffix": ". ", 
                            "form": "verb-short", 
                            "text-case": "lowercase"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "name", 
                          "attrs": {
                            "and": "text", 
                            "delimiter": ", "
                          }
                        }
                      ], 
                      "name": "names", 
                      "attrs": {
                        "variable": "translator", 
                        "delimiter": ", "
                      }
                    }
                  ], 
                  "name": "if", 
                  "attrs": {
                    "variable": "author editor", 
                    "match": "any"
                  }
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "editor-translator"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "editor-translator"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter", 
                "match": "none"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "secondary-contributors-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "editor-translator"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "container-contributors-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [
                                {
                                  "children": [], 
                                  "name": "label", 
                                  "attrs": {
                                    "prefix": " ", 
                                    "suffix": " ", 
                                    "form": "verb", 
                                    "text-case": "capitalize-first"
                                  }
                                }, 
                                {
                                  "children": [], 
                                  "name": "name", 
                                  "attrs": {
                                    "and": "text", 
                                    "delimiter": ", "
                                  }
                                }
                              ], 
                              "name": "names", 
                              "attrs": {
                                "variable": "editor", 
                                "delimiter": ". "
                              }
                            }
                          ], 
                          "name": "if", 
                          "attrs": {
                            "variable": "author"
                          }
                        }
                      ], 
                      "name": "choose", 
                      "attrs": {}
                    }, 
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [
                                {
                                  "children": [], 
                                  "name": "label", 
                                  "attrs": {
                                    "prefix": " ", 
                                    "suffix": " ", 
                                    "form": "verb", 
                                    "text-case": "capitalize-first"
                                  }
                                }, 
                                {
                                  "children": [], 
                                  "name": "name", 
                                  "attrs": {
                                    "and": "text", 
                                    "delimiter": ", "
                                  }
                                }
                              ], 
                              "name": "names", 
                              "attrs": {
                                "variable": "translator", 
                                "delimiter": ". "
                              }
                            }
                          ], 
                          "name": "if", 
                          "attrs": {
                            "variable": "author editor", 
                            "match": "any"
                          }
                        }
                      ], 
                      "name": "choose", 
                      "attrs": {}
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ". "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter", 
                "match": "none"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "secondary-contributors"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [
                                {
                                  "children": [], 
                                  "name": "label", 
                                  "attrs": {
                                    "suffix": " ", 
                                    "form": "verb", 
                                    "text-case": "lowercase"
                                  }
                                }, 
                                {
                                  "children": [], 
                                  "name": "name", 
                                  "attrs": {
                                    "and": "text", 
                                    "delimiter": ", "
                                  }
                                }
                              ], 
                              "name": "names", 
                              "attrs": {
                                "variable": "editor", 
                                "delimiter": ", "
                              }
                            }
                          ], 
                          "name": "if", 
                          "attrs": {
                            "variable": "author"
                          }
                        }
                      ], 
                      "name": "choose", 
                      "attrs": {}
                    }, 
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [
                                {
                                  "children": [], 
                                  "name": "label", 
                                  "attrs": {
                                    "suffix": " ", 
                                    "form": "verb", 
                                    "text-case": "lowercase"
                                  }
                                }, 
                                {
                                  "children": [], 
                                  "name": "name", 
                                  "attrs": {
                                    "and": "text", 
                                    "delimiter": ", "
                                  }
                                }
                              ], 
                              "name": "names", 
                              "attrs": {
                                "variable": "translator", 
                                "delimiter": ", "
                              }
                            }
                          ], 
                          "name": "if", 
                          "attrs": {
                            "variable": "author editor", 
                            "match": "any"
                          }
                        }
                      ], 
                      "name": "choose", 
                      "attrs": {}
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ", "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "container-contributors"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", "
              }
            }, 
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": ", ", 
                "suffix": ".", 
                "form": "short"
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "editor"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "editor-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", "
              }
            }, 
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": ", ", 
                "suffix": ".", 
                "form": "verb-short"
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "translator"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "translator-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": " ", 
                "suffix": " ", 
                "form": "verb", 
                "text-case": "lowercase"
              }
            }, 
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", "
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "recipient", 
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "recipient-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", "
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "editor-note"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "translator-note"
                  }
                }
              ], 
              "name": "substitute", 
              "attrs": {}
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "author"
          }
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "macro": "recipient-note"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "contributors-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", ", 
                "delimiter-precedes-last": "always", 
                "name-as-sort-order": "first"
              }
            }, 
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": ", ", 
                "suffix": ".", 
                "form": "short"
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "editor"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "editor"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", ", 
                "delimiter-precedes-last": "always", 
                "name-as-sort-order": "first"
              }
            }, 
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": ", ", 
                "suffix": ".", 
                "form": "verb-short"
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "translator"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "translator"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "genre", 
                            "text-case": "capitalize-first"
                          }
                        }
                      ], 
                      "name": "if", 
                      "attrs": {
                        "variable": "genre"
                      }
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "term": "letter", 
                            "text-case": "capitalize-first"
                          }
                        }
                      ], 
                      "name": "else", 
                      "attrs": {}
                    }
                  ], 
                  "name": "choose", 
                  "attrs": {}
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "personal_communication"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "macro": "recipient-note", 
            "prefix": " "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "recipient"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", ", 
                "delimiter-precedes-last": "always", 
                "name-as-sort-order": "first"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "editor"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "translator"
                  }
                }
              ], 
              "name": "substitute", 
              "attrs": {}
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "author"
          }
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "macro": "recipient", 
            "prefix": ". "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "contributors"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": " ", 
                "suffix": " ", 
                "form": "verb", 
                "text-case": "lowercase"
              }
            }, 
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "form": "short"
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "recipient"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "recipient-short"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "form": "short"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "names", 
                  "attrs": {
                    "variable": "editor"
                  }
                }, 
                {
                  "children": [], 
                  "name": "names", 
                  "attrs": {
                    "variable": "translator"
                  }
                }
              ], 
              "name": "substitute", 
              "attrs": {}
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "author"
          }
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "macro": "recipient-short"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "contributors-short"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", ", 
                "sort-separator": ", ", 
                "delimiter-precedes-last": "always", 
                "name-as-sort-order": "all"
              }
            }, 
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": ", ", 
                "suffix": ".", 
                "form": "verb-short"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "names", 
                  "attrs": {
                    "variable": "editor"
                  }
                }, 
                {
                  "children": [], 
                  "name": "names", 
                  "attrs": {
                    "variable": "translator"
                  }
                }
              ], 
              "name": "substitute", 
              "attrs": {}
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "author"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "contributors-sort"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": " ", 
                "suffix": " ", 
                "form": "verb", 
                "text-case": "lowercase"
              }
            }, 
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", "
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "interviewer", 
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "interviewer-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "label", 
              "attrs": {
                "prefix": " ", 
                "suffix": " ", 
                "form": "verb", 
                "text-case": "capitalize-first"
              }
            }, 
            {
              "children": [], 
              "name": "name", 
              "attrs": {
                "and": "text", 
                "delimiter": ", "
              }
            }
          ], 
          "name": "names", 
          "attrs": {
            "variable": "interviewer", 
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "interviewer"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "genre"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "variable": "title", 
                "match": "none"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "title", 
                    "font-style": "italic"
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "book"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "title", 
                    "quotes": "true"
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "title-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "genre", 
                            "text-case": "capitalize-first"
                          }
                        }
                      ], 
                      "name": "if", 
                      "attrs": {
                        "type": "personal_communication", 
                        "match": "none"
                      }
                    }
                  ], 
                  "name": "choose", 
                  "attrs": {}
                }
              ], 
              "name": "if", 
              "attrs": {
                "variable": "title", 
                "match": "none"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "title", 
                    "font-style": "italic"
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "book"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "title", 
                    "quotes": "true"
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "title"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "term": "interview", 
                            "text-case": "lowercase"
                          }
                        }
                      ], 
                      "name": "if", 
                      "attrs": {
                        "type": "interview"
                      }
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "genre", 
                            "form": "short"
                          }
                        }
                      ], 
                      "name": "else-if", 
                      "attrs": {
                        "type": "manuscript speech", 
                        "match": "any"
                      }
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "issued"
                          }
                        }
                      ], 
                      "name": "else-if", 
                      "attrs": {
                        "type": "personal_communication"
                      }
                    }
                  ], 
                  "name": "choose", 
                  "attrs": {}
                }
              ], 
              "name": "if", 
              "attrs": {
                "variable": "title", 
                "match": "none"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "title", 
                    "font-style": "italic", 
                    "form": "short"
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "book"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "title", 
                    "quotes": "true", 
                    "form": "short"
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "title-short"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "interviewer-note"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "medium"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "if", 
                  "attrs": {
                    "variable": "title", 
                    "match": "none"
                  }
                }, 
                {
                  "children": [], 
                  "name": "else-if", 
                  "attrs": {
                    "type": "thesis speech", 
                    "match": "any"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "variable": "genre"
                      }
                    }
                  ], 
                  "name": "else", 
                  "attrs": {}
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "description-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "interviewer"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "medium", 
                    "text-case": "capitalize-first"
                  }
                }
              ], 
              "name": "group", 
              "attrs": {
                "delimiter": ". "
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "if", 
                  "attrs": {
                    "variable": "title", 
                    "match": "none"
                  }
                }, 
                {
                  "children": [], 
                  "name": "else-if", 
                  "attrs": {
                    "type": "thesis speech", 
                    "match": "any"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "variable": "genre", 
                        "text-case": "capitalize-first"
                      }
                    }
                  ], 
                  "name": "else", 
                  "attrs": {}
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "description"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "term": "in", 
                    "suffix": " ", 
                    "text-case": "lowercase"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "variable": "container-title", 
            "font-style": "italic"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "container-title-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "term": "in", 
                    "suffix": " ", 
                    "text-case": "capitalize-first"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "variable": "container-title", 
            "font-style": "italic"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "container-title"
      }
    }, 
    {
      "children": [
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "variable": "collection-title"
          }
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "variable": "collection-number", 
            "prefix": " "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "collection-title"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [], 
                              "name": "number", 
                              "attrs": {
                                "variable": "edition", 
                                "form": "ordinal"
                              }
                            }, 
                            {
                              "children": [], 
                              "name": "text", 
                              "attrs": {
                                "term": "edition", 
                                "suffix": ".", 
                                "form": "short"
                              }
                            }
                          ], 
                          "name": "group", 
                          "attrs": {
                            "delimiter": " "
                          }
                        }
                      ], 
                      "name": "if", 
                      "attrs": {
                        "is-numeric": "edition"
                      }
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "edition", 
                            "suffix": "."
                          }
                        }
                      ], 
                      "name": "else", 
                      "attrs": {}
                    }
                  ], 
                  "name": "choose", 
                  "attrs": {}
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "book chapter", 
                "match": "any"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "edition-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [], 
                              "name": "number", 
                              "attrs": {
                                "variable": "edition", 
                                "form": "ordinal"
                              }
                            }, 
                            {
                              "children": [], 
                              "name": "text", 
                              "attrs": {
                                "term": "edition", 
                                "suffix": ".", 
                                "form": "short"
                              }
                            }
                          ], 
                          "name": "group", 
                          "attrs": {
                            "delimiter": " "
                          }
                        }
                      ], 
                      "name": "if", 
                      "attrs": {
                        "is-numeric": "edition"
                      }
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "edition", 
                            "suffix": ".", 
                            "text-case": "capitalize-first"
                          }
                        }
                      ], 
                      "name": "else", 
                      "attrs": {}
                    }
                  ], 
                  "name": "choose", 
                  "attrs": {}
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "book chapter", 
                "match": "any"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "edition"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "volume", 
                    "prefix": " "
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "issue", 
                    "prefix": ", no. "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-journal"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "term": "volume", 
                            "suffix": ". ", 
                            "form": "short"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "number", 
                          "attrs": {
                            "variable": "volume", 
                            "form": "numeric"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {}
                    }, 
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [
                                {
                                  "children": [], 
                                  "name": "number", 
                                  "attrs": {
                                    "variable": "number-of-volumes", 
                                    "form": "numeric"
                                  }
                                }, 
                                {
                                  "children": [], 
                                  "name": "text", 
                                  "attrs": {
                                    "prefix": " ", 
                                    "plural": "true", 
                                    "term": "volume", 
                                    "form": "short", 
                                    "suffix": "."
                                  }
                                }
                              ], 
                              "name": "group", 
                              "attrs": {}
                            }
                          ], 
                          "name": "if", 
                          "attrs": {
                            "variable": "locator", 
                            "match": "none"
                          }
                        }
                      ], 
                      "name": "choose", 
                      "attrs": {}
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "edition-note"
                      }
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ", ", 
                    "prefix": ", "
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "book chapter", 
                "match": "any"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "locators-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "volume", 
                    "prefix": " "
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "issue", 
                    "prefix": ", no. "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-journal"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "term": "volume", 
                            "suffix": ". ", 
                            "form": "short", 
                            "text-case": "capitalize-first"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "number", 
                          "attrs": {
                            "variable": "volume", 
                            "form": "numeric"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {}
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "number", 
                          "attrs": {
                            "variable": "number-of-volumes", 
                            "form": "numeric"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "prefix": " ", 
                            "plural": "true", 
                            "term": "volume", 
                            "form": "short", 
                            "suffix": "."
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {}
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "edition"
                      }
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ". ", 
                    "prefix": ". "
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "book", 
                "match": "any"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "locators"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "edition", 
                            "suffix": " "
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "prefix": " ", 
                            "term": "edition"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {}
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "term": "section", 
                            "suffix": ". ", 
                            "form": "short"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "section"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {}
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ", "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-newspaper"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "locators-newspaper"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "term": "presented at", 
                "suffix": " "
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "event"
              }
            }
          ], 
          "name": "group", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "event"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "publisher-place"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "publisher"
              }
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ": "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "publisher"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "month", 
                        "suffix": " "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "day", 
                        "suffix": ", "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "year"
                      }
                    }
                  ], 
                  "name": "date", 
                  "attrs": {
                    "variable": "issued"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "graphic report", 
                "match": "any"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "year"
                      }
                    }
                  ], 
                  "name": "date", 
                  "attrs": {
                    "variable": "issued"
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "book chapter thesis", 
                "match": "any"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "month", 
                        "suffix": " "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "day", 
                        "suffix": ", "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "date-part", 
                      "attrs": {
                        "name": "year"
                      }
                    }
                  ], 
                  "name": "date", 
                  "attrs": {
                    "variable": "issued"
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "issued"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "label", 
                      "attrs": {
                        "variable": "locator", 
                        "form": "short", 
                        "strip-periods": "false", 
                        "suffix": " "
                      }
                    }
                  ], 
                  "name": "if", 
                  "attrs": {
                    "locator": "page", 
                    "match": "none"
                  }
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "locator"
              }
            }
          ], 
          "name": "group", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "point-locators-subsequent"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "pages"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "variable": "locator", 
                "match": "none"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "locator", 
                    "prefix": ": "
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "article-journal"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "point-locators-subsequent", 
                    "prefix": ", "
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "point-locators"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "page", 
                    "prefix": ": "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-journal"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "page", 
                    "prefix": ", "
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "chapter"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "pages"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "volume", 
                    "suffix": ":"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "page"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "chapter"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "locators-chapter"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "page", 
                    "prefix": ": "
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-journal"
              }
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "locators-journal"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "archive_location"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "archive"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "archive-place"
              }
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "archive-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "archive_location", 
                "text-case": "capitalize-first"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "archive"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "archive-place"
              }
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ". "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "archive"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "issued", 
                    "prefix": " (", 
                    "suffix": ")"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-journal"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [], 
                              "name": "if", 
                              "attrs": {
                                "variable": "title", 
                                "match": "none"
                              }
                            }, 
                            {
                              "children": [
                                {
                                  "children": [], 
                                  "name": "text", 
                                  "attrs": {
                                    "variable": "genre"
                                  }
                                }
                              ], 
                              "name": "else-if", 
                              "attrs": {
                                "type": "thesis speech", 
                                "match": "any"
                              }
                            }
                          ], 
                          "name": "choose", 
                          "attrs": {}
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "event"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {
                        "delimiter": " "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "publisher"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "issued"
                      }
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ", ", 
                    "prefix": " (", 
                    "suffix": ")"
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "variable": "publisher-place publisher", 
                "match": "any"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "issued", 
                    "prefix": ", "
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "issue-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "issued", 
                    "prefix": " (", 
                    "suffix": ")"
                  }
                }
              ], 
              "name": "if", 
              "attrs": {
                "type": "article-journal"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "if", 
                      "attrs": {
                        "variable": "title", 
                        "match": "none"
                      }
                    }, 
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "variable": "genre", 
                            "prefix": ". ", 
                            "text-case": "capitalize-first"
                          }
                        }
                      ], 
                      "name": "else", 
                      "attrs": {}
                    }
                  ], 
                  "name": "choose", 
                  "attrs": {}
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "event", 
                    "prefix": " "
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "variable": "event-place", 
                    "prefix": ", "
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "issued", 
                    "prefix": ", "
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "type": "speech"
              }
            }, 
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [
                            {
                              "children": [], 
                              "name": "text", 
                              "attrs": {
                                "variable": "genre", 
                                "text-case": "capitalize-first"
                              }
                            }
                          ], 
                          "name": "if", 
                          "attrs": {
                            "type": "thesis"
                          }
                        }
                      ], 
                      "name": "choose", 
                      "attrs": {}
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "publisher"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "issued"
                      }
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ", ", 
                    "prefix": ". "
                  }
                }
              ], 
              "name": "else-if", 
              "attrs": {
                "variable": "publisher-place publisher", 
                "match": "any"
              }
            }, 
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "issued", 
                    "prefix": ", "
                  }
                }
              ], 
              "name": "else", 
              "attrs": {}
            }
          ], 
          "name": "choose", 
          "attrs": {}
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "issue"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "archive-note"
                      }
                    }
                  ], 
                  "name": "if", 
                  "attrs": {
                    "type": "graphic report", 
                    "match": "any"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "archive-note"
                      }
                    }
                  ], 
                  "name": "else-if", 
                  "attrs": {
                    "type": "book thesis chapter article-journal article-newspaper article-magazine", 
                    "match": "none"
                  }
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "DOI", 
                "prefix": "doi:"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "URL"
              }
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ", "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "access-note"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "archive"
                      }
                    }
                  ], 
                  "name": "if", 
                  "attrs": {
                    "type": "graphic report", 
                    "match": "any"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "archive"
                      }
                    }
                  ], 
                  "name": "else-if", 
                  "attrs": {
                    "type": "book thesis chapter article-journal article-newspaper article-magazine", 
                    "match": "none"
                  }
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "variable": "URL"
              }
            }
          ], 
          "name": "group", 
          "attrs": {
            "delimiter": ". "
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "access"
      }
    }, 
    {
      "children": [
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "macro": "contributors-sort", 
            "suffix": " "
          }
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "variable": "title", 
            "suffix": " "
          }
        }, 
        {
          "children": [], 
          "name": "text", 
          "attrs": {
            "variable": "genre"
          }
        }
      ], 
      "name": "macro", 
      "attrs": {
        "name": "sort-key"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "term": "ibid", 
                            "suffix": ".", 
                            "text-case": "capitalize-first"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "point-locators-subsequent"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {
                        "delimiter": ", "
                      }
                    }
                  ], 
                  "name": "if", 
                  "attrs": {
                    "position": "ibid-with-locator"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "term": "ibid", 
                        "suffix": ".", 
                        "text-case": "capitalize-first"
                      }
                    }
                  ], 
                  "name": "else-if", 
                  "attrs": {
                    "position": "ibid"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "contributors-short"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "title-short"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "point-locators-subsequent"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {
                        "delimiter": ", "
                      }
                    }
                  ], 
                  "name": "else-if", 
                  "attrs": {
                    "position": "subsequent"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "contributors-note"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "title-note"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "description-note"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "secondary-contributors-note"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "container-title-note"
                          }
                        }, 
                        {
                          "children": [], 
                          "name": "text", 
                          "attrs": {
                            "macro": "container-contributors-note"
                          }
                        }
                      ], 
                      "name": "group", 
                      "attrs": {
                        "delimiter": ", "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "locators-note"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "collection-title", 
                        "prefix": ", "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "issue-note"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "locators-newspaper", 
                        "prefix": ", "
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "point-locators"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "access-note", 
                        "prefix": ", "
                      }
                    }
                  ], 
                  "name": "else", 
                  "attrs": {}
                }
              ], 
              "name": "choose", 
              "attrs": {}
            }
          ], 
          "name": "layout", 
          "attrs": {
            "delimiter": "; ", 
            "prefix": "", 
            "suffix": "."
          }
        }
      ], 
      "name": "citation", 
      "attrs": {
        "et-al-subsequent-min": "4", 
        "et-al-min": "4", 
        "et-al-subsequent-use-first": "1", 
        "et-al-use-first": "1", 
        "disambiguate-add-names": "true"
      }
    }, 
    {
      "children": [
        {
          "children": [
            {
              "children": [], 
              "name": "key", 
              "attrs": {
                "macro": "sort-key"
              }
            }, 
            {
              "children": [], 
              "name": "key", 
              "attrs": {
                "variable": "issued"
              }
            }
          ], 
          "name": "sort", 
          "attrs": {}
        }, 
        {
          "children": [
            {
              "children": [
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "contributors"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "title"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "description"
                  }
                }, 
                {
                  "children": [], 
                  "name": "text", 
                  "attrs": {
                    "macro": "secondary-contributors"
                  }
                }, 
                {
                  "children": [
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "container-title"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "container-contributors"
                      }
                    }, 
                    {
                      "children": [], 
                      "name": "text", 
                      "attrs": {
                        "macro": "locators-chapter"
                      }
                    }
                  ], 
                  "name": "group", 
                  "attrs": {
                    "delimiter": ", "
                  }
                }
              ], 
              "name": "group", 
              "attrs": {
                "delimiter": ". "
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "locators"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "collection-title", 
                "prefix": ". "
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "issue"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "locators-newspaper", 
                "prefix": ", "
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "locators-journal"
              }
            }, 
            {
              "children": [], 
              "name": "text", 
              "attrs": {
                "macro": "access", 
                "prefix": ". "
              }
            }
          ], 
          "name": "layout", 
          "attrs": {
            "suffix": "."
          }
        }
      ], 
      "name": "bibliography", 
      "attrs": {
        "et-al-min": "11", 
        "et-al-use-first": "7", 
        "entry-spacing": "0", 
        "subsequent-author-substitute": "---", 
        "hanging-indent": "true"
      }
    }
  ], 
  "name": "style", 
  "attrs": {
    "xmlns": "http://purl.org/net/xbiblio/csl", 
    "class": "note", 
    //"xml:lang": "en"
  }
}
