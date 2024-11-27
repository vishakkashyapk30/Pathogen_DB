from flask import Flask, jsonify, request, render_template
import pymysql
from datetime import datetime
import os

DB_NAME = 'Pathogen'
app = Flask(__name__, static_url_path='/static')

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="agn1705mY5ql",
        database="pathogen"
    )

# Serve index page
@app.route('/')
def index():
    return render_template('index.html')

def query_primary_keys(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get primary key columns
        cursor.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'")
        output = cursor.fetchall()
        
        KCOLUMN_NAME = 4     # 4-th index
        primary_keys = [row[KCOLUMN_NAME] for row in output]
        print(primary_keys)
        
        return primary_keys
    except Exception as e:
        print(f"error: {e}")
        return list()
    finally:
        conn.close()

@app.route('/api/get_primary_keys/<table>', methods=['GET'])
def get_primary_keys(table):
    try:
        primary_keys = query_primary_keys(table)
        # print(primary_keys)
        return jsonify({'status': 'success', 'primary_keys': primary_keys})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/get/<table>', methods=['POST'])
def get_data(table):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        data = request.json
        where_clause = " AND ".join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values())

        # Fetch the record matching the composite key
        cursor.execute(f"SELECT * FROM {table} WHERE {where_clause}", values)
        result = cursor.fetchone()

        if not result:
            return jsonify({'status': 'error', 'message': 'No matching record found'}), 404

        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/check_constraints/<table>', methods=['POST'])
def check_constraints(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data = request.json
        
        # primary key where clause
        # primary_key_attr = query_primary_keys(table)
        # primary_key_val = [data[key] for key in primary_key_attr]
        # where_clause = " AND ".join([f"{table}.{col} = %s" for col in primary_key_attr])
        # values = tuple(data.values())
        # print(f"{values=}")

        # Check for dependent records in foreign key tables
        cursor.execute(f"""
            SELECT 
                rc.TABLE_NAME AS Dependent_Table,
                rc.DELETE_RULE AS Delete_Rule,
                rc.CONSTRAINT_NAME AS Constraint_Name,
                kcu.COLUMN_NAME AS Dependent_Column,
                kcu.REFERENCED_COLUMN_NAME AS Referenced_Column
            FROM 
                information_schema.REFERENTIAL_CONSTRAINTS rc
            JOIN 
                information_schema.KEY_COLUMN_USAGE kcu
                ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                AND rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
            WHERE 
                rc.REFERENCED_TABLE_NAME = %s
                AND rc.CONSTRAINT_SCHEMA = %s;
        """, (table, DB_NAME))
        constraints = cursor.fetchall()
        print(f"{constraints=}")
        
        cascade_triggers = []
        restrict_triggers = []
        (
            KDEPENDENT_TABLE, KDELETE_RULE, KCONSTRAINT_NAME, KDEPENDENT_COLUMN, KREFERENCED_COLUMN 
        ) = (
            0, 1, 2, 3, 4
        )
        
        for constraint in constraints:
            if constraint[KDELETE_RULE] in ('CASCADE', 'RESTRICT', 'NO ACTION'):
                dependent_table = constraint[KDEPENDENT_TABLE]
                dependent_col = constraint[KDEPENDENT_COLUMN]
                referenced_col = constraint[KREFERENCED_COLUMN]
                print(f"{dependent_table=}, {dependent_col=}, {referenced_col=}")
                
                cursor.execute(f"""
                    SELECT 1 FROM {dependent_table}
                    WHERE {dependent_table}.{dependent_col} = %s LIMIT 1
                    """, (data[referenced_col],))
                if cursor.fetchone():
                    if constraint[KDELETE_RULE] == 'CASCADE':
                        cascade_triggers.append({'table': dependent_table})
                    else:
                        # restrict is same as no action for foreign key constraints
                        # we have no other referential constraint than foreign keys anyway
                        restrict_triggers.append({'table': dependent_table})
                

        warning_resp = {
            'status': 'warning',
            'message': '',
            'cascade_t' : False,
            'restrict_t' : False,
        }
        
        if restrict_triggers:
            warning_resp['restrict_t'] = True
            warning_resp['restrict_triggers'] = restrict_triggers
            warning_resp['message'] = 'Will trigger RESTRICT constraint on given record(s).'
        
        if cascade_triggers:
            warning_resp['cascade_t'] = True
            warning_resp['cascade_triggers'] = cascade_triggers
            if warning_resp['restrict_t']:
                warning_resp['message'] += ' Will trigger CASCADE, as well.'
            else:
                warning_resp['message'] += 'Will trigger CASCADE constraint on given record(s).'
        
        if warning_resp['cascade_t'] or warning_resp['restrict_t']:
            return jsonify(warning_resp)
        
        return jsonify({'status': 'success', 'message': 'No constraints will be triggered'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# Get table schema
@app.route('/api/table-schema/<table>')
def get_table_schema(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get column information
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        
        schema = []
        for col in columns:
            field = {
                'name': col[0],
                'type': 'text',  # default
                'required': col[2] == 'NO'
            }
            
            # Set appropriate field type
            if 'int' in col[1].lower():
                field['type'] = 'number'
            elif 'date' in col[1].lower():
                field['type'] = 'date'
            
            # Add constraints
            if col[1].lower().startswith('decimal'):
                field['type'] = 'number'
                field['step'] = '0.01'
            
            schema.append(field)
        
        return jsonify(schema)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# CRUD Operations
@app.route('/api/insert/<table>', methods=['POST'])
def insert_data(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        data = request.json
        # print(data)
        columns = [key for key in data.keys() if str(data[key])]   # "if str(data[key]) is something"
        # print(columns)
        # print(tuple([data[key] for key in columns]))
        colstring = ', '.join(columns)
        values = ', '.join(['%s'] * len(columns))
        sql = f"INSERT INTO {table} ({colstring}) VALUES ({values})"
        
        cursor.execute(sql, tuple(data[key] for key in columns))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Data inserted successfully'})
    except Exception as e:
        conn.rollback()
        print("error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/update/<table>', methods=['POST'])
def update_data(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        data = request.json
        print("no error here")
        primary_key_attr = query_primary_keys(table)
        primary_key_val = [data.pop(key) for key in primary_key_attr]
        print("we reached here")
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        where_clause = ' AND '.join([f"{key} = %s" for key in primary_key_attr])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        print(sql)
        print(tuple(data.values()) + tuple(primary_key_val))
        print(sql % (tuple(data.values()) + tuple(primary_key_val)))
        
        cursor.execute(sql, tuple(data.values()) + tuple(primary_key_val))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Data updated successfully'})
    except Exception as e:
        conn.rollback()
        print(f"update_data error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/delete/<table>', methods=['POST'])
def delete_data(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        data = request.json
        # print("no error here")
        primary_key_attr = query_primary_keys(table)
        primary_key_val = [data.pop(attr) for attr in primary_key_attr]
        # print("we reached here")
        
        where_clause = ' AND '.join([f"{key} = %s" for key in primary_key_attr])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        print(sql % tuple(primary_key_val))
        
        cursor.execute(sql, tuple(primary_key_val))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Data deleted successfully'})
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# Read table data
@app.route('/api/read/<table>', methods=['GET'])
def read_table(table):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# Update specific attribute
@app.route('/api/update/<table>', methods=['POST'])
def update_attribute(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data = request.json
        column_to_update = data.get('column')
        value = data.get('value')
        identifier_column = data.get('identifier_column')
        identifier_value = data.get('identifier_value')

        sql = f"UPDATE {table} SET {column_to_update} = %s WHERE {identifier_column} = %s"
        cursor.execute(sql, (value, identifier_value))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Record updated successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# Delete specific row
# @app.route('/api/delete/<table>', methods=['POST'])
# def delete_row(table):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     try:
#         data = request.json
#         identifier_column = data.get('identifier_column')
#         identifier_value = data.get('identifier_value')

#         sql = f"DELETE FROM {table} WHERE {identifier_column} = %s"
#         cursor.execute(sql, (identifier_value,))
#         conn.commit()
#         return jsonify({'status': 'success', 'message': 'Record deleted successfully'})
#     except Exception as e:
#         conn.rollback()
#         return jsonify({'status': 'error', 'message': str(e)}), 500
#     finally:
#         conn.close()

# Analysis Routes
@app.route('/api/analysis/high-risk')
def analysis_high_risk():
    threshold = request.args.get('threshold', default=0, type=float)
    return get_high_risk_pathogens(threshold)

# @app.route('/api/analysis/research-labs')
# def analysis_research_labs():
#     pathogen_type = request.args.get('pathogen_type', default='', type=str)
#     return get_labs_by_pathogen_type(pathogen_type)

@app.route('/api/analysis/vaccine-distribution')
def analysis_vaccine_distribution():
    return get_vaccine_distribution_stats()

@app.route('/api/analysis/mutation-impact')
def analysis_mutation_impact():
    return get_mutation_impact()

@app.route('/api/analysis/project-success')
def analysis_project_success():
    return get_project_success_metrics()

# Existing Query Endpoints
@app.route('/api/high_risk_pathogens/<float:threshold>')
def get_high_risk_pathogens(threshold):
    try:
        if not (0 <= threshold <= 100):
            return jsonify({'error': 'Threshold must be between 0 and 100'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT id, scientific_name, type, lethality_rate, mutation_probability 
            FROM Pathogen 
            WHERE mutation_probability > %s
            ORDER BY mutation_probability DESC
        """, (threshold/100,))  # Convert percentage to decimal
        
        result = cursor.fetchall()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/api/labs_by_pathogen_type/<pathogen_type>')
# def get_labs_by_pathogen_type(pathogen_type):
#     conn = get_db_connection()
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
    
#     cursor.execute("""
#         SELECT DISTINCT rl.lab_id, rl.name, rl.total_funding, c.name as country
#         FROM Research_lab rl
#         JOIN Research_focus rf ON rl.lab_id = rf.lab_id
#         JOIN Pathogen p ON rf.pathogen_id = p.id
#         JOIN Country c ON rl.location = c.country_id
#         WHERE p.type = %s
#     """, (pathogen_type,))
    
#     result = cursor.fetchall()
#     conn.close()
#     return jsonify(result)

@app.route('/api/vaccine_distribution_stats')
def get_vaccine_distribution_stats():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT 
            c.name as country_name,
            COUNT(DISTINCT gvd.vaccine_id) as vaccines_received,
            SUM(gvd.doses_distributed) as total_doses,
            AVG(gvd.coverage_percentage) as avg_coverage
        FROM Country c
        JOIN Global_vaccine_distribution gvd ON c.country_id = gvd.importer_id
        GROUP BY c.country_id, c.name
        ORDER BY avg_coverage DESC
    """)
    
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)

@app.route('/api/mutation_impact')
def get_mutation_impact():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT 
            m.mutation_id,
            p1.scientific_name as original_pathogen,
            p1.lethality_rate as original_lethality,
            p2.scientific_name as mutated_pathogen,
            p2.lethality_rate as mutated_lethality,
            CONCAT(m.year, '-', m.month, '-', m.day) as mutation_date
        FROM Mutation m
        JOIN Pathogen p1 ON m.parent_pathogen_id = p1.id
        JOIN Pathogen p2 ON m.mutation_id = CONCAT(p2.id, '/', p1.id)
        ORDER BY m.year DESC, m.month DESC, m.day DESC
    """)
    
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)

@app.route('/api/project_success_metrics')
def get_project_success_metrics():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT 
            rp.project_id,
            ra.research_aim,
            v.effectiveness as vaccine_effectiveness,
            v.number_of_administrations,
            pul.funding_allocated,
            rl.name as research_lab
        FROM Research_project rp
        JOIN Research_aim ra ON rp.project_id = ra.project_id
        LEFT JOIN Vaccine v ON rp.project_id = v.project_id
        JOIN Project_under_lab pul ON rp.project_id = pul.project_id
        JOIN Research_lab rl ON pul.lab_id = rl.lab_id
        ORDER BY v.effectiveness DESC
    """)
    
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)

@app.route('/api/analysis/high-severity-countries')
def analysis_high_severity_countries():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT COUNT(DISTINCT gr.country_id) AS high_severity_country_count
            FROM Government_response gr
            JOIN Response_effect re ON gr.response_id = re.response_id
            JOIN Pathogen p ON re.pathogen_id = p.id
            WHERE re.response_severity = 'High' AND p.lethality_rate > 0
        """)
        
        result = cursor.fetchone()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/analysis/airborne-pathogen-funding')
def analysis_airborne_pathogen_funding():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT SUM(pul.funding_allocated) AS total_airborne_funding
            FROM Project_under_lab pul
            JOIN Research_project rp ON pul.project_id = rp.project_id
            JOIN Pathogen p ON rp.pathogen_id = p.id
            WHERE p.transmission_method = 'Airborne'
        """)
        
        result = cursor.fetchone()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route('/api/tables', methods=['GET'])
def get_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        return jsonify(tables)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# New Routes
@app.route('/api/tables/columns', methods=['GET'])
def get_table_columns():
    table = request.args.get('table')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DESCRIBE {table}")
        columns = [col[0] for col in cursor.fetchall()]
        return jsonify(columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/selection', methods=['POST'])
def perform_selection():
    data = request.json
    table = data.get('table')
    column = data.get('column')
    condition = data.get('condition')
    value = data.get('value')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        query = f"SELECT * FROM {table} WHERE {column} {condition} %s"
        cursor.execute(query, (value,))
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/projection', methods=['POST'])
def perform_projection():
    data = request.json
    table = data.get('table')
    columns = data.get('columns', [])

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        query = f"SELECT {', '.join(columns)} FROM {table}"
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/aggregation', methods=['POST'])
def perform_aggregation():
    data = request.json
    table = data.get('table')
    column = data.get('column')
    operation = data.get('operation')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        query = f"SELECT {operation}({column}) as result FROM {table}"
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/search', methods=['POST'])
def perform_search():
    data = request.json
    table = data.get('table')
    column = data.get('column')
    pattern = data.get('pattern')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        query = f"SELECT * FROM {table} WHERE {column} LIKE %s"
        cursor.execute(query, (f'%{pattern}%',))
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)