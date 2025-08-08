#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating RDM search mapping.

This module provides a preset that modifies search mapping to RDM compatibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RDMMappingPreset(Preset):
    """Preset for record service class."""

    modifies = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        parent_mapping = {
            "mappings": {
                "dynamic_templates": [
                    {
                        "pids": {
                            "path_match": "pids.*",
                            "match_mapping_type": "object",
                            "mapping": {
                                "type": "object",
                                "properties": {
                                    "identifier": {
                                        "type": "text",
                                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                                    },
                                    "provider": {"type": "keyword"},
                                    "client": {"type": "keyword"},
                                },
                            },
                        }
                    },
                    {
                        "parent_pids": {
                            "path_match": "parent.pids.*",
                            "match_mapping_type": "object",
                            "mapping": {
                                "type": "object",
                                "properties": {
                                    "identifier": {
                                        "type": "text",
                                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                                    },
                                    "provider": {"type": "keyword"},
                                    "client": {"type": "keyword"},
                                },
                            },
                        }
                    },
                    {
                        "i18n_title": {
                            "path_match": "*.title.*",
                            "unmatch": "(metadata.title)|(metadata.additional_titles.title)",
                            "match_mapping_type": "object",
                            "mapping": {
                                "type": "text",
                                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                            },
                        }
                    },
                ],
                "properties": {
                    "is_published": {"type": "boolean"},
                    "custom_fields": {"type": "object", "dynamic": "true"},
                    "access": {
                        "type": "object",
                        "properties": {
                            "embargo": {
                                "type": "object",
                                "properties": {
                                    "active": {"type": "boolean"},
                                    "reason": {"type": "text"},
                                    "until": {"type": "date", "format": "basic_date||strict_date"},
                                },
                            },
                            "files": {"type": "keyword", "ignore_above": 1024},
                            "record": {"type": "keyword", "ignore_above": 1024},
                            "status": {"type": "keyword", "ignore_above": 1024},
                        },
                    },
                    "deletion_status": {"type": "keyword", "ignore_above": 1024},
                    "is_deleted": {"type": "boolean"},
                    "pids": {"type": "object", "dynamic": "true"},
                    "parent": {
                        "properties": {
                            "access": {
                                "properties": {
                                    "owned_by": {"properties": {"user": {"type": "keyword"}}},
                                    "grants": {
                                        "properties": {
                                            "subject": {
                                                "properties": {"type": {"type": "keyword"}, "id": {"type": "keyword"}}
                                            },
                                            "permission": {"type": "keyword"},
                                            "origin": {"type": "keyword"},
                                        }
                                    },
                                    "grant_tokens": {"type": "keyword"},
                                    "links": {"properties": {"id": {"type": "keyword"}}},
                                    "settings": {
                                        "properties": {
                                            "allow_user_requests": {"type": "boolean"},
                                            "allow_guest_requests": {"type": "boolean"},
                                            "accept_conditions_text": {"type": "text"},
                                            "secret_link_expiration": {"type": "integer"},
                                        }
                                    },
                                }
                            },
                            "communities": {
                                "properties": {
                                    "ids": {"type": "keyword"},
                                    "default": {"type": "keyword"},
                                    "entries": {
                                        "type": "object",
                                        "properties": {
                                            "uuid": {"type": "keyword"},
                                            "created": {"type": "date"},
                                            "updated": {"type": "date"},
                                            "version_id": {"type": "long"},
                                            "id": {"type": "keyword"},
                                            "is_verified": {"type": "boolean"},
                                            "@v": {"type": "keyword"},
                                            "slug": {"type": "keyword"},
                                            "children": {"properties": {"allow": {"type": "boolean"}}},
                                            "metadata": {
                                                "properties": {
                                                    "title": {"type": "text"},
                                                    "type": {
                                                        "type": "object",
                                                        "properties": {
                                                            "@v": {"type": "keyword"},
                                                            "id": {"type": "keyword"},
                                                            "title": {
                                                                "type": "object",
                                                                "dynamic": "true",
                                                                "properties": {"en": {"type": "text"}},
                                                            },
                                                        },
                                                    },
                                                    "organizations": {
                                                        "type": "object",
                                                        "properties": {
                                                            "@v": {"type": "keyword"},
                                                            "id": {"type": "keyword"},
                                                            "name": {"type": "text"},
                                                        },
                                                    },
                                                    "funding": {
                                                        "properties": {
                                                            "award": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "@v": {"type": "keyword"},
                                                                    "id": {"type": "keyword"},
                                                                    "title": {"type": "object", "dynamic": "true"},
                                                                    "number": {
                                                                        "type": "text",
                                                                        "fields": {"keyword": {"type": "keyword"}},
                                                                    },
                                                                    "program": {"type": "keyword"},
                                                                    "acronym": {
                                                                        "type": "keyword",
                                                                        "fields": {"text": {"type": "text"}},
                                                                    },
                                                                    "identifiers": {
                                                                        "properties": {
                                                                            "identifier": {"type": "keyword"},
                                                                            "scheme": {"type": "keyword"},
                                                                        }
                                                                    },
                                                                },
                                                            },
                                                            "funder": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "@v": {"type": "keyword"},
                                                                    "id": {"type": "keyword"},
                                                                    "name": {"type": "text"},
                                                                },
                                                            },
                                                        }
                                                    },
                                                    "website": {"type": "keyword"},
                                                }
                                            },
                                            "theme": {
                                                "type": "object",
                                                "properties": {
                                                    "enabled": {"type": "boolean"},
                                                    "brand": {"type": "keyword"},
                                                    "style": {"type": "object", "enabled": False},
                                                },
                                            },
                                            "parent": {
                                                "type": "object",
                                                "properties": {
                                                    "uuid": {"type": "keyword"},
                                                    "created": {"type": "date"},
                                                    "updated": {"type": "date"},
                                                    "version_id": {"type": "long"},
                                                    "id": {"type": "keyword"},
                                                    "is_verified": {"type": "boolean"},
                                                    "@v": {"type": "keyword"},
                                                    "slug": {"type": "keyword"},
                                                    "children": {"properties": {"allow": {"type": "boolean"}}},
                                                    "metadata": {
                                                        "type": "object",
                                                        "properties": {
                                                            "title": {"type": "text"},
                                                            "type": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "@v": {"type": "keyword"},
                                                                    "id": {"type": "keyword"},
                                                                    "title": {
                                                                        "type": "object",
                                                                        "dynamic": "true",
                                                                        "properties": {"en": {"type": "text"}},
                                                                    },
                                                                },
                                                            },
                                                            "website": {"type": "keyword"},
                                                            "organizations": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "@v": {"type": "keyword"},
                                                                    "id": {"type": "keyword"},
                                                                    "name": {"type": "text"},
                                                                },
                                                            },
                                                            "funding": {
                                                                "properties": {
                                                                    "award": {
                                                                        "type": "object",
                                                                        "properties": {
                                                                            "@v": {"type": "keyword"},
                                                                            "id": {"type": "keyword"},
                                                                            "title": {
                                                                                "type": "object",
                                                                                "dynamic": "true",
                                                                            },
                                                                            "number": {
                                                                                "type": "text",
                                                                                "fields": {
                                                                                    "keyword": {"type": "keyword"}
                                                                                },
                                                                            },
                                                                            "program": {"type": "keyword"},
                                                                            "acronym": {
                                                                                "type": "keyword",
                                                                                "fields": {"text": {"type": "text"}},
                                                                            },
                                                                            "identifiers": {
                                                                                "properties": {
                                                                                    "identifier": {"type": "keyword"},
                                                                                    "scheme": {"type": "keyword"},
                                                                                }
                                                                            },
                                                                        },
                                                                    },
                                                                    "funder": {
                                                                        "type": "object",
                                                                        "properties": {
                                                                            "@v": {"type": "keyword"},
                                                                            "id": {"type": "keyword"},
                                                                            "name": {"type": "text"},
                                                                        },
                                                                    },
                                                                }
                                                            },
                                                        },
                                                    },
                                                    "theme": {
                                                        "type": "object",
                                                        "properties": {
                                                            "enabled": {"type": "boolean"},
                                                            "brand": {"type": "keyword"},
                                                            "style": {"type": "object", "enabled": False},
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                }
                            },
                            "pids": {"type": "object", "dynamic": "true"},
                            "is_verified": {"type": "boolean"},
                        }
                    },
                    "internal_notes": {  # only published?
                        "type": "object",
                        "properties": {
                            "id": {"type": "keyword"},
                            "note": {"type": "text"},
                            "timestamp": {"type": "date"},
                            "added_by": {"type": "object", "properties": {"user": {"type": "keyword"}}},
                        },
                    },
                    "metadata": {
                        "properties": {
                            "_default_preview": {"type": "object", "enabled": False},
                            "_internal_notes": {
                                "properties": {
                                    "note": {"type": "text"},
                                    "timestamp": {"type": "date"},
                                    "user": {"type": "keyword"},
                                }
                            },
                            "contact": {"type": "keyword"},
                            "contributors": {
                                "properties": {
                                    "affiliations": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "name": {"type": "text"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "keyword"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                        },
                                    },
                                    "person_or_org": {
                                        "properties": {
                                            "family_name": {"type": "text"},
                                            "given_name": {"type": "text"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "keyword"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                            "name": {"type": "text"},
                                            "type": {"type": "keyword"},
                                        }
                                    },
                                    "role": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                }
                            },
                            "creators": {
                                "properties": {
                                    "affiliations": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "name": {"type": "text"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "keyword"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                        },
                                    },
                                    "person_or_org": {
                                        "properties": {
                                            "family_name": {"type": "text"},
                                            "given_name": {"type": "text"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "keyword"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                            "name": {"type": "text"},
                                            "type": {"type": "keyword"},
                                        }
                                    },
                                    "role": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                }
                            },
                            "dates": {
                                "properties": {
                                    "description": {"type": "text"},
                                    "date": {"type": "keyword"},
                                    "date_range": {"type": "date_range"},
                                    "type": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                }
                            },
                            "description": {"type": "text"},
                            "additional_descriptions": {
                                "properties": {
                                    "description": {"type": "text"},
                                    "lang": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                    "type": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                }
                            },
                            "formats": {"type": "keyword"},
                            "funding": {
                                "properties": {
                                    "award": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                            "number": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                                            "acronym": {"type": "keyword", "fields": {"text": {"type": "text"}}},
                                            "program": {"type": "keyword"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "text"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                        },
                                    },
                                    "funder": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "name": {"type": "text"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "keyword"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                        },
                                    },
                                }
                            },
                            "identifiers": {
                                "properties": {"identifier": {"type": "text"}, "scheme": {"type": "keyword"}}
                            },
                            "languages": {
                                "type": "object",
                                "properties": {
                                    "@v": {"type": "keyword"},
                                    "id": {"type": "keyword"},
                                    "title": {"type": "object", "dynamic": "true"},
                                },
                            },
                            "locations": {
                                "properties": {
                                    "features": {
                                        "properties": {
                                            "centroid": {"type": "geo_point"},
                                            "geometry": {"type": "geo_shape"},
                                            "place": {"type": "text"},
                                            "identifiers": {
                                                "properties": {
                                                    "identifier": {"type": "keyword"},
                                                    "scheme": {"type": "keyword"},
                                                }
                                            },
                                            "description": {"type": "text"},
                                        }
                                    }
                                }
                            },
                            "publication_date": {"type": "keyword"},
                            "publication_date_range": {"type": "date_range"},
                            "publisher": {
                                "type": "text",
                                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                            },
                            "references": {
                                "properties": {
                                    "identifier": {"type": "keyword"},
                                    "reference": {"type": "text"},
                                    "scheme": {"type": "keyword"},
                                }
                            },
                            "related_identifiers": {
                                "properties": {
                                    "identifier": {"type": "keyword"},
                                    "relation_type": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                    "resource_type": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                    "scheme": {"type": "keyword"},
                                }
                            },
                            "resource_type": {
                                "type": "object",
                                "properties": {
                                    "@v": {"type": "keyword"},
                                    "id": {"type": "keyword"},
                                    "title": {"type": "object", "dynamic": "true"},
                                    "props": {
                                        "type": "object",
                                        "properties": {"type": {"type": "keyword"}, "subtype": {"type": "keyword"}},
                                    },
                                },
                            },
                            "rights": {
                                "type": "object",
                                "properties": {
                                    "@v": {"type": "keyword"},
                                    "id": {"type": "keyword"},
                                    "title": {"type": "object", "dynamic": "true"},
                                    "description": {"type": "object", "dynamic": "true"},
                                    "props": {
                                        "type": "object",
                                        "properties": {"url": {"type": "keyword"}, "scheme": {"type": "keyword"}},
                                    },
                                    "link": {"type": "keyword", "index": False},
                                    "icon": {"type": "keyword", "index": False},
                                },
                            },
                            "sizes": {"type": "keyword", "ignore_above": 256},
                            "subjects": {
                                "type": "object",
                                "properties": {
                                    "@v": {"type": "keyword"},
                                    "id": {"type": "keyword"},
                                    "subject": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                                    "scheme": {"type": "keyword"},
                                },
                            },
                            "combined_subjects": {"type": "keyword"},
                            "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                            "additional_titles": {
                                "properties": {
                                    "lang": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                    "title": {"type": "text"},
                                    "type": {
                                        "type": "object",
                                        "properties": {
                                            "@v": {"type": "keyword"},
                                            "id": {"type": "keyword"},
                                            "title": {"type": "object", "dynamic": "true"},
                                        },
                                    },
                                }
                            },
                            "version": {"type": "keyword"},
                        }
                    },
                },
            }
        }

        """
        # old
        "bucket_id": {"type": "keyword", "index": False},
        "versions": {
            "properties": {
                "index": {"type": "integer"},
                "is_latest": {"type": "boolean"},
                "is_latest_draft": {"type": "boolean"},
                "latest_id": {"type": "keyword"},
                "latest_index": {"type": "integer"},
                "next_draft_id": {"type": "keyword"},
            }
        },
        "has_draft": {"type": "boolean"},
        "record_status": {"type": "keyword"},
        "pid": {
            "properties": {
                "obj_type": {"type": "keyword", "index": False},
                "pid_type": {"type": "keyword", "index": False},
                "pk": {"type": "long", "index": False},
                "status": {"type": "keyword", "index": False},
            }
        },
        "fork_version_id": {"type": "long"},
        "parent": {
            "properties": {
                "$schema": {"type": "keyword", "index": False},
                "id": {"type": "keyword"},
                "uuid": {"type": "keyword", "index": False},
                "version_id": {"type": "long"},
                "created": {"type": "date"},
                "updated": {"type": "date"},
                "pid": {
                    "properties": {
                        "obj_type": {"type": "keyword", "index": False},
                        "pid_type": {"type": "keyword", "index": False},
                        "pk": {"type": "long", "index": False},
                        "status": {"type": "keyword", "index": False},
                    }
                },
            }
        }
        """

        yield PatchJSONFile(
            "draft-mapping",
            parent_mapping,
        )

        yield PatchJSONFile(
            "record-mapping",
            parent_mapping,
        )
