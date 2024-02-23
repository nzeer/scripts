#------------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# utils.pyx
#
# Cython file for utility functions (embedded in thick_impl.pyx).
#------------------------------------------------------------------------------

cdef object _convert_from_json_node(dpiJsonNode *node):
    cdef:
        dpiTimestamp *as_timestamp
        dpiIntervalDS *as_interval
        dpiJsonArray *array
        dpiBytes *as_bytes
        dpiJsonObject *obj
        dict dict_value
        list list_value
        int32_t seconds
        DbType dbtype
        uint32_t i
        str key
    if node.nativeTypeNum == DPI_NATIVE_TYPE_NULL:
        return None
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_NUMBER:
        if node.nativeTypeNum == DPI_NATIVE_TYPE_DOUBLE:
            return node.value.asDouble
        elif node.nativeTypeNum == DPI_NATIVE_TYPE_FLOAT:
            return node.value.asFloat
        as_bytes = &node.value.asBytes
        return PY_TYPE_DECIMAL(as_bytes.ptr[:as_bytes.length].decode())
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_VARCHAR:
        as_bytes = &node.value.asBytes
        return as_bytes.ptr[:as_bytes.length].decode()
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_RAW:
        return node.value.asBytes.ptr[:node.value.asBytes.length]
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_DATE \
            or node.oracleTypeNum == DPI_ORACLE_TYPE_TIMESTAMP:
        as_timestamp = &node.value.asTimestamp
        return cydatetime.datetime_new(as_timestamp.year, as_timestamp.month,
                                       as_timestamp.day, as_timestamp.hour,
                                       as_timestamp.minute,
                                       as_timestamp.second,
                                       as_timestamp.fsecond // 1000, None)
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_BOOLEAN:
        return node.value.asBoolean
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_INTERVAL_DS:
        as_interval = &node.value.asIntervalDS
        seconds = as_interval.hours * 60 * 60 + as_interval.minutes * 60 + \
                as_interval.seconds
        return cydatetime.timedelta_new(as_interval.days, seconds,
                                        as_interval.fseconds // 1000)
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_JSON_OBJECT:
        obj = &node.value.asJsonObject
        dict_value = {}
        for i in range(obj.numFields):
            key = obj.fieldNames[i][:obj.fieldNameLengths[i]].decode()
            dict_value[key] = _convert_from_json_node(&obj.fields[i])
        return dict_value
    elif node.oracleTypeNum == DPI_ORACLE_TYPE_JSON_ARRAY:
        array = &node.value.asJsonArray
        list_value = [None] * array.numElements
        for i in range(array.numElements):
            list_value[i] = _convert_from_json_node(&array.elements[i])
        return list_value
    dbtype = DbType._from_num(node.oracleTypeNum)
    errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED, name=dbtype.name)


cdef int _convert_from_python(object value, DbType dbtype,
                              ThickDbObjectTypeImpl obj_type_impl,
                              dpiDataBuffer *dbvalue, StringBuffer buf,
                              ThickVarImpl var_impl=None,
                              uint32_t pos=0) except -1:
    cdef:
        uint32_t oracle_type = dbtype.num
        ThickDbObjectImpl obj_impl
        dpiTimestamp *timestamp
        ThickLobImpl lob_impl
        int seconds, status
        JsonBuffer json_buf
    if oracle_type == DPI_ORACLE_TYPE_NUMBER:
        if isinstance(value, bool):
            if value:
                buf.set_value("1")
            else:
                buf.set_value("0")
        elif isinstance(value, (int, float, PY_TYPE_DECIMAL)):
            buf.set_value((<str> cpython.PyObject_Str(value)).encode())
        else:
            message = f"expecting number, got {type(value)}"
            raise TypeError(message)
        dbvalue.asBytes.ptr = buf.ptr
        dbvalue.asBytes.length = buf.length
    elif oracle_type == DPI_ORACLE_TYPE_NATIVE_DOUBLE \
            or oracle_type == DPI_ORACLE_TYPE_NATIVE_FLOAT:
        if oracle_type == DPI_ORACLE_TYPE_NATIVE_DOUBLE:
            dbvalue.asDouble = <double> value
        else:
            dbvalue.asFloat = <float> value
    elif oracle_type == DPI_ORACLE_TYPE_VARCHAR \
            or oracle_type == DPI_ORACLE_TYPE_NVARCHAR \
            or oracle_type == DPI_ORACLE_TYPE_CHAR \
            or oracle_type == DPI_ORACLE_TYPE_NCHAR \
            or oracle_type == DPI_ORACLE_TYPE_LONG_VARCHAR:
        buf.set_value(value)
        dbvalue.asBytes.ptr = buf.ptr
        dbvalue.asBytes.length = buf.length
    elif oracle_type == DPI_ORACLE_TYPE_RAW \
            or oracle_type == DPI_ORACLE_TYPE_LONG_RAW:
        buf.set_value(value)
        dbvalue.asBytes.ptr = buf.ptr
        dbvalue.asBytes.length = buf.length
    elif oracle_type == DPI_ORACLE_TYPE_DATE \
            or oracle_type == DPI_ORACLE_TYPE_TIMESTAMP \
            or oracle_type == DPI_ORACLE_TYPE_TIMESTAMP_LTZ \
            or oracle_type == DPI_ORACLE_TYPE_TIMESTAMP_TZ:
        memset(&dbvalue.asTimestamp, 0, sizeof(dbvalue.asTimestamp))
        timestamp = &dbvalue.asTimestamp
        timestamp.year = cydatetime.PyDateTime_GET_YEAR(value)
        timestamp.month = cydatetime.PyDateTime_GET_MONTH(value)
        timestamp.day = cydatetime.PyDateTime_GET_DAY(value)
        if cydatetime.PyDateTime_Check(value):
            timestamp.hour = cydatetime.PyDateTime_DATE_GET_HOUR(value)
            timestamp.minute = cydatetime.PyDateTime_DATE_GET_MINUTE(value)
            timestamp.second = cydatetime.PyDateTime_DATE_GET_SECOND(value)
            timestamp.fsecond = \
                    cydatetime.PyDateTime_DATE_GET_MICROSECOND(value) * 1000
    elif oracle_type == DPI_ORACLE_TYPE_BOOLEAN:
        dbvalue.asBoolean = <bint> value
    elif oracle_type == DPI_ORACLE_TYPE_NATIVE_INT:
        if isinstance(value, bool):
            dbvalue.asInt64 = 1 if value else 0
        else:
            dbvalue.asInt64 = <int64_t> value
    elif oracle_type == DPI_ORACLE_TYPE_INTERVAL_DS:
        seconds = cydatetime.timedelta_seconds(value)
        dbvalue.asIntervalDS.days = cydatetime.timedelta_days(value)
        dbvalue.asIntervalDS.hours = seconds // 3600
        seconds = seconds % 3600
        dbvalue.asIntervalDS.minutes = seconds // 60
        dbvalue.asIntervalDS.seconds = seconds % 60
        dbvalue.asIntervalDS.fseconds = \
                cydatetime.timedelta_microseconds(value) * 1000
    elif oracle_type == DPI_ORACLE_TYPE_OBJECT:
        if not isinstance(value, PY_TYPE_DB_OBJECT):
            raise TypeError("expecting DbObject")
        obj_impl = <ThickDbObjectImpl> value._impl
        if var_impl is not None:
            if dpiVar_setFromObject(var_impl._handle, pos,
                                    obj_impl._handle) < 0:
                _raise_from_odpi()
        else:
            dbvalue.asObject = obj_impl._handle
    elif oracle_type == DPI_ORACLE_TYPE_CLOB \
            or oracle_type == DPI_ORACLE_TYPE_BLOB \
            or oracle_type == DPI_ORACLE_TYPE_NCLOB:
        if isinstance(value, PY_TYPE_LOB):
            lob_impl = value._impl
            if var_impl is not None:
                if dpiVar_setFromLob(var_impl._handle, pos,
                                     lob_impl._handle) < 0:
                    _raise_from_odpi()
            else:
                dbvalue.asLOB = lob_impl._handle
        else:
            buf.set_value(value)
            dbvalue.asBytes.ptr = buf.ptr
            dbvalue.asBytes.length = buf.length
    elif oracle_type == DPI_ORACLE_TYPE_JSON:
        json_buf = JsonBuffer()
        json_buf.from_object(value)
        if dpiJson_setValue(dbvalue.asJson, &json_buf._top_node) < 0:
            _raise_from_odpi()
    else:
        errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED, name=dbtype.name)


cdef object _convert_oci_attr_to_python(uint32_t attr_type,
                                        dpiDataBuffer *value,
                                        uint32_t value_len):
    """
    Convert an OCI attribute value to a Python value.
    """
    if attr_type == PYO_OCI_ATTR_TYPE_STRING:
        if value.asString == NULL:
            return None
        return value.asString[:value_len].decode()
    elif attr_type == PYO_OCI_ATTR_TYPE_BOOLEAN:
        return value.asBoolean
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT8:
        return value.asUint8
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT16:
        return value.asUint16
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT32:
        return value.asUint32
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT64:
        return value.asUint64
    errors._raise_err(errors.ERR_INVALID_OCI_ATTR_TYPE, attr_type=attr_type)


cdef int _convert_python_to_oci_attr(object value, uint32_t attr_type,
                                     StringBuffer str_buf,
                                     dpiDataBuffer *oci_buf,
                                     void **oci_value,
                                     uint32_t *oci_len) except -1:
    """
    Convert a Python value to the format required by an OCI attribute.
    """
    if attr_type == PYO_OCI_ATTR_TYPE_STRING:
        str_buf.set_value(value)
        oci_value[0] = str_buf.ptr
        oci_len[0] = str_buf.length
    elif attr_type == PYO_OCI_ATTR_TYPE_BOOLEAN:
        oci_buf.asBoolean = value
        oci_value[0] = &oci_buf.asBoolean
        oci_len[0] = sizeof(oci_buf.asBoolean)
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT8:
        oci_buf.asUint8 = value
        oci_value[0] = &oci_buf.asUint8
        oci_len[0] = sizeof(oci_buf.asUint8)
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT16:
        oci_buf.asUint16 = value
        oci_value[0] = &oci_buf.asUint16
        oci_len[0] = sizeof(oci_buf.asUint16)
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT32:
        oci_buf.asUint32 = value
        oci_value[0] = &oci_buf.asUint32
        oci_len[0] = sizeof(oci_buf.asUint32)
    elif attr_type == PYO_OCI_ATTR_TYPE_UINT64:
        oci_buf.asUint64 = value
        oci_value[0] = &oci_buf.asUint64
        oci_len[0] = sizeof(oci_buf.asUint64)
    else:
        errors._raise_err(errors.ERR_INVALID_OCI_ATTR_TYPE,
                          attr_type=attr_type)


cdef object _convert_to_python(ThickConnImpl conn_impl, DbType dbtype,
                               ThickDbObjectTypeImpl obj_type_impl,
                               dpiDataBuffer *dbvalue,
                               int preferred_num_type=NUM_TYPE_FLOAT,
                               bint bypass_decode=False,
                               const char* encoding_errors=NULL):
    cdef:
        uint32_t oracle_type = dbtype.num
        ThickDbObjectImpl obj_impl
        dpiTimestamp *as_timestamp
        dpiJsonNode *json_node
        ThickLobImpl lob_impl
        uint32_t rowid_length
        dpiBytes *as_bytes
        const char *rowid
        int32_t seconds
    if bypass_decode:
        oracle_type = DPI_ORACLE_TYPE_RAW
    if oracle_type == DPI_ORACLE_TYPE_CHAR \
            or oracle_type == DPI_ORACLE_TYPE_NCHAR \
            or oracle_type == DPI_ORACLE_TYPE_VARCHAR \
            or oracle_type == DPI_ORACLE_TYPE_NVARCHAR \
            or oracle_type == DPI_ORACLE_TYPE_LONG_VARCHAR \
            or oracle_type == DPI_ORACLE_TYPE_LONG_NVARCHAR \
            or oracle_type == DPI_ORACLE_TYPE_XMLTYPE:
        as_bytes = &dbvalue.asBytes
        return as_bytes.ptr[:as_bytes.length].decode("utf-8", encoding_errors)
    elif oracle_type == DPI_ORACLE_TYPE_NUMBER:
        as_bytes = &dbvalue.asBytes
        if preferred_num_type == NUM_TYPE_INT \
                and memchr(as_bytes.ptr, b'.', as_bytes.length) == NULL:
            return int(as_bytes.ptr[:as_bytes.length])
        elif preferred_num_type == NUM_TYPE_DECIMAL:
            return PY_TYPE_DECIMAL(as_bytes.ptr[:as_bytes.length].decode())
        return float(as_bytes.ptr[:as_bytes.length])
    elif oracle_type == DPI_ORACLE_TYPE_RAW \
            or oracle_type == DPI_ORACLE_TYPE_LONG_RAW:
        as_bytes = &dbvalue.asBytes
        return as_bytes.ptr[:as_bytes.length]
    elif oracle_type == DPI_ORACLE_TYPE_DATE \
            or oracle_type == DPI_ORACLE_TYPE_TIMESTAMP \
            or oracle_type == DPI_ORACLE_TYPE_TIMESTAMP_LTZ \
            or oracle_type == DPI_ORACLE_TYPE_TIMESTAMP_TZ:
        as_timestamp = &dbvalue.asTimestamp
        return cydatetime.datetime_new(as_timestamp.year, as_timestamp.month,
                                       as_timestamp.day, as_timestamp.hour,
                                       as_timestamp.minute,
                                       as_timestamp.second,
                                       as_timestamp.fsecond // 1000, None)
    elif oracle_type == DPI_ORACLE_TYPE_BOOLEAN:
        return dbvalue.asBoolean == 1
    elif oracle_type == DPI_ORACLE_TYPE_NATIVE_DOUBLE:
        return dbvalue.asDouble
    elif oracle_type == DPI_ORACLE_TYPE_NATIVE_FLOAT:
        return dbvalue.asFloat
    elif oracle_type == DPI_ORACLE_TYPE_NATIVE_INT:
        return dbvalue.asInt64
    elif oracle_type == DPI_ORACLE_TYPE_ROWID:
        if dpiRowid_getStringValue(dbvalue.asRowid, &rowid, &rowid_length) < 0:
            _raise_from_odpi()
        return rowid[:rowid_length].decode()
    elif oracle_type == DPI_ORACLE_TYPE_CLOB \
            or oracle_type == DPI_ORACLE_TYPE_BLOB \
            or oracle_type == DPI_ORACLE_TYPE_NCLOB \
            or oracle_type == DPI_ORACLE_TYPE_BFILE:
        lob_impl = ThickLobImpl._create(conn_impl, dbtype, dbvalue.asLOB)
        return PY_TYPE_LOB._from_impl(lob_impl)
    elif oracle_type == DPI_ORACLE_TYPE_OBJECT:
        obj_impl = ThickDbObjectImpl.__new__(ThickDbObjectImpl)
        obj_impl.type = obj_type_impl
        if dpiObject_addRef(dbvalue.asObject) < 0:
            _raise_from_odpi()
        obj_impl._handle = dbvalue.asObject
        return PY_TYPE_DB_OBJECT._from_impl(obj_impl)
    elif oracle_type == DPI_ORACLE_TYPE_INTERVAL_DS:
        seconds = dbvalue.asIntervalDS.hours * 60 * 60 + \
                dbvalue.asIntervalDS.minutes * 60 + \
                dbvalue.asIntervalDS.seconds
        return cydatetime.timedelta_new(dbvalue.asIntervalDS.days, seconds,
                                        dbvalue.asIntervalDS.fseconds // 1000)
    elif oracle_type == DPI_ORACLE_TYPE_JSON:
        if dpiJson_getValue(dbvalue.asJson, DPI_JSON_OPT_NUMBER_AS_STRING,
                            &json_node) < 0:
            _raise_from_odpi()
        return _convert_from_json_node(json_node)
    errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED, name=dbtype.name)

cdef uint32_t _get_native_type_num(DbType dbtype):
    cdef uint32_t oracle_type_num = dbtype.num
    if oracle_type_num == DPI_ORACLE_TYPE_NATIVE_FLOAT:
        return DPI_NATIVE_TYPE_FLOAT
    elif oracle_type_num == DPI_ORACLE_TYPE_NATIVE_DOUBLE:
        return DPI_NATIVE_TYPE_DOUBLE
    elif oracle_type_num == DPI_ORACLE_TYPE_BOOLEAN:
        return DPI_NATIVE_TYPE_BOOLEAN
    elif oracle_type_num == DPI_ORACLE_TYPE_CLOB \
            or oracle_type_num == DPI_ORACLE_TYPE_NCLOB \
            or oracle_type_num == DPI_ORACLE_TYPE_BLOB \
            or oracle_type_num == DPI_ORACLE_TYPE_BFILE:
        return DPI_NATIVE_TYPE_LOB
    elif oracle_type_num == DPI_ORACLE_TYPE_DATE \
            or oracle_type_num == DPI_ORACLE_TYPE_TIMESTAMP \
            or oracle_type_num == DPI_ORACLE_TYPE_TIMESTAMP_LTZ \
            or oracle_type_num == DPI_ORACLE_TYPE_TIMESTAMP_TZ:
        return DPI_NATIVE_TYPE_TIMESTAMP
    elif oracle_type_num == DPI_ORACLE_TYPE_STMT:
        return DPI_NATIVE_TYPE_STMT
    elif oracle_type_num == DPI_ORACLE_TYPE_NATIVE_INT:
        return DPI_NATIVE_TYPE_INT64
    elif oracle_type_num == DPI_ORACLE_TYPE_OBJECT:
        return DPI_NATIVE_TYPE_OBJECT
    elif oracle_type_num == DPI_ORACLE_TYPE_ROWID:
        return DPI_NATIVE_TYPE_ROWID
    elif oracle_type_num == DPI_ORACLE_TYPE_INTERVAL_DS:
        return DPI_NATIVE_TYPE_INTERVAL_DS
    elif oracle_type_num == DPI_ORACLE_TYPE_JSON:
        return DPI_NATIVE_TYPE_JSON
    return DPI_NATIVE_TYPE_BYTES

cdef list _string_list_to_python(dpiStringList *str_list):
    """
    Converts the contents of dpiStringList to a Python list of strings.
    """
    cdef:
        list result
        uint32_t i
        str temp
    try:
        result = cpython.PyList_New(str_list.numStrings)
        for i in range(str_list.numStrings):
            temp = str_list.strings[i][:str_list.stringLengths[i]].decode()
            cpython.Py_INCREF(temp)
            cpython.PyList_SET_ITEM(result, i, temp)
        return result
    finally:
        if dpiContext_freeStringList(driver_context, str_list) < 0:
            _raise_from_odpi()

cdef object _create_new_from_info(dpiErrorInfo *error_info):
    """
    Creates a new error object given a dpiErrorInfo structure
    that is already populated with error information.
    """
    cdef bytes msg_bytes = error_info.message[:error_info.messageLength]
    context = "%s: %s" % (error_info.fnName, error_info.action)
    return errors._Error(msg_bytes.decode(), context, code=error_info.code,
                         offset=error_info.offset,
                         isrecoverable=error_info.isRecoverable,
                         iswarning=error_info.isWarning)


cdef int _raise_from_info(dpiErrorInfo *error_info) except -1:
    """
    Raises an exception given a dpiErrorInfo structure that is already
    populated with error information.
    """
    error = _create_new_from_info(error_info)
    exc_type = get_exception_class(error_info.code)
    raise exc_type(error)


cdef int _raise_from_odpi() except -1:
    """
    Raises an exception from ODPI-C, given that an error has been raised by
    ODPI-C (a return code of -1 has been received).
    """
    cdef dpiErrorInfo error_info
    dpiContext_getError(driver_context, &error_info)
    _raise_from_info(&error_info)


def clientversion():
    """
    Returns the version of the Oracle Client library being used as a 5-tuple.
    The five values are the major version, minor version, update number, patch
    number and port update number.
    """
    if driver_context == NULL:
        errors._raise_err(errors.ERR_INIT_ORACLE_CLIENT_NOT_CALLED)
    return (
        client_version_info.versionNum,
        client_version_info.releaseNum,
        client_version_info.updateNum,
        client_version_info.portReleaseNum,
        client_version_info.portUpdateNum
    )


def init_oracle_client(lib_dir=None, config_dir=None, error_url=None,
                       driver_name=None):
    """
    Initialize the Oracle Client library. This method is available externally
    in order to be called with parameters that control how the Oracle Client
    library is initialized. If not called earlier, the first usage of the
    Oracle Client library will cause this method to be called internally.
    """
    cdef:
        bytes lib_dir_bytes, config_dir_bytes, driver_name_bytes
        dpiContextCreateParams params
        dpiErrorInfo error_info
        bytes encoding_bytes
    global driver_context_params
    params_tuple = (lib_dir, config_dir, error_url, driver_name)
    if driver_context != NULL:
        if params_tuple != driver_context_params:
            errors._raise_err(errors.ERR_LIBRARY_ALREADY_INITIALIZED)
        return
    with driver_mode.get_manager(requested_thin_mode=False) as mode_mgr:
        memset(&params, 0, sizeof(dpiContextCreateParams))
        encoding_bytes = constants.ENCODING.encode()
        params.defaultEncoding = encoding_bytes
        if config_dir is None:
            config_dir = defaults.config_dir
        if lib_dir is not None:
            lib_dir_bytes = lib_dir.encode()
            params.oracleClientLibDir = lib_dir_bytes
        if config_dir is not None:
            config_dir_bytes = config_dir.encode()
            params.oracleClientConfigDir = config_dir_bytes
        if driver_name is None:
            driver_name = f"{constants.DRIVER_NAME} thk : {VERSION}"
        driver_name_bytes = driver_name.encode()[:30]
        params.defaultDriverName = driver_name_bytes
        if error_url is not None:
            error_url_bytes = error_url.encode()
        else:
            error_url_bytes = constants.INSTALLATION_URL.encode()
        params.loadErrorUrl = error_url_bytes
        if dpiContext_createWithParams(DPI_MAJOR_VERSION, DPI_MINOR_VERSION,
                                       &params, &driver_context,
                                       &error_info) < 0:
            _raise_from_info(&error_info)
        if dpiContext_getClientVersion(driver_context,
                                       &client_version_info) < 0:
            _raise_from_odpi()
        driver_context_params = params_tuple


def init_thick_impl(package):
    """
    Initializes globals after the package has been completely initialized. This
    is to avoid circular imports and eliminate the need for global lookups.
    """
    global PY_TYPE_DB_OBJECT, PY_TYPE_LOB
    PY_TYPE_DB_OBJECT = package.DbObject
    PY_TYPE_LOB = package.LOB
