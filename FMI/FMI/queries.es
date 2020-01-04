
GET recipes/_search
{
    "size" : 1000,
    "_source" : ["id", "cooking_clubs.cooking_date"],
    "query": {
        "bool": {
            "filter": [
                {
                    "nested": {
                        "path": "cooking_clubs",
                        "query": {
                            "range": {
                                "cooking_clubs.cooking_date": {
                                    "gte": "2019-01-01"
                                }
                            }
                        }
                    }
                }
            ]
        }
    }
}
