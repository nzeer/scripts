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
# var.pyx
#
# Cython file defining the thick Variable implementation class (embedded in
# thick_impl.pyx).
#------------------------------------------------------------------------------

cdef class ThickVarImpl(BaseVarImpl):
    cdef:
        dpiVar *_handle
        dpiData *_data
        StringBuffer _buf
        uint32_t _native_type_num
        bint _get_returned_data
        object _conn

    def __dealloc__(self):
        if self._handle != NULL:
            dpiVar_release(self._handle)

    cdef int _bind(self, object conn, BaseCursorImpl cursor_impl,
                   uint32_t num_execs, object name, uint32_t pos) except -1:
        cdef:
            ThickCursorImpl thick_cursor_impl = <ThickCursorImpl> cursor_impl
            uint32_t name_length, i
            dpiDataBuffer *dbvalue
            const char *name_ptr
            bytes name_bytes
        if self._native_type_num == DPI_NATIVE_TYPE_STMT:
            for i in range(self.num_elements):
                if self._data[i].isNull:
                    continue
                dbvalue = &self._data[i].value
                if dbvalue.asStmt == thick_cursor_impl._handle:
                    errors._raise_err(errors.ERR_SELF_BIND_NOT_SUPPORTED)
        if name is not None:
            name_bytes = name.encode()
            name_ptr = name_bytes
            name_length = <uint32_t> len(name_bytes)
            if dpiStmt_bindByName(thick_cursor_impl._handle, name_ptr,
                                  name_length, self._handle) < 0:
                _raise_from_odpi()
        else:
            if dpiStmt_bindByPos(thick_cursor_impl._handle, pos,
                                 self._handle) < 0:
                _raise_from_odpi()
        if thick_cursor_impl._stmt_info.isReturning and not self._is_value_set:
            self._get_returned_data = True
        self._is_value_set = False

    cdef int _create_handle(self) except -1:
        cdef:
             ThickConnImpl conn_impl = self._conn_impl
             dpiObjectType *obj_type_handle = NULL
             ThickDbObjectTypeImpl obj_type_impl
        if self._handle != NULL:
             dpiVar_release(self._handle)
             self._handle = NULL
        if self.objtype is not None:
             obj_type_impl = <ThickDbObjectTypeImpl> self.objtype
             obj_type_handle = obj_type_impl._handle
        self._native_type_num = _get_native_type_num(self.dbtype)
        if dpiConn_newVar(conn_impl._handle, self.dbtype.num,
                          self._native_type_num, self.num_elements, self.size,
                          0, self.is_array, obj_type_handle, &self._handle,
                          &self._data) < 0:
             _raise_from_odpi()

    cdef int _finalize_init(self) except -1:
        """
        Internal method that finalizes initialization of the variable.
        """
        BaseVarImpl._finalize_init(self)
        self._create_handle()

    cdef list _get_array_value(self):
        """
        Internal method to return the value of the array.
        """
        cdef uint32_t i
        return [self._get_scalar_value(i) \
                for i in range(self.num_elements_in_array)]

    cdef object _get_cursor_value(self, dpiDataBuffer *dbvalue):
        cdef:
            ThickCursorImpl cursor_impl
            object cursor
        cursor = self._conn.cursor()
        cursor_impl = <ThickCursorImpl> cursor._impl
        if dpiStmt_addRef(dbvalue.asStmt) < 0:
            _raise_from_odpi()
        cursor_impl._handle = dbvalue.asStmt
        cursor_impl._fixup_ref_cursor = True
        return cursor

    cdef object _get_scalar_value(self, uint32_t pos):
        """
        Internal method to return the value of the variable at the given
        position.
        """
        cdef:
            uint32_t num_returned_rows
            dpiData *returned_data
        if self._get_returned_data:
            if dpiVar_getReturnedData(self._handle, pos, &num_returned_rows,
                                      &returned_data) < 0:
                _raise_from_odpi()
            return self._transform_array_to_python(num_returned_rows,
                                                   returned_data)
        return self._transform_element_to_python(pos, self._data)

    cdef int _on_reset_bind(self, uint32_t num_rows) except -1:
        """
        Called when the bind variable is being reset, just prior to performing
        a bind operation.
        """
        cdef:
            dpiStmtInfo stmt_info
            uint32_t i
        BaseVarImpl._on_reset_bind(self, num_rows)
        if self._native_type_num == DPI_NATIVE_TYPE_STMT:
            for i in range(self.num_elements):
                if self._data[i].isNull:
                    continue
                if dpiStmt_getInfo(self._data[i].value.asStmt, &stmt_info) < 0:
                    self._create_handle()
                    break

    cdef int _resize(self, uint32_t new_size) except -1:
        """
        Resize the variable to the new size provided.
        """
        cdef:
            dpiVar *orig_handle = NULL
            uint32_t num_elements, i
            dpiData *source_data
            dpiData *orig_data
        BaseVarImpl._resize(self, new_size)
        orig_data = self._data
        orig_handle = self._handle
        self._handle = NULL
        try:
            self._create_handle()
            if self.is_array:
                if dpiVar_getNumElementsInArray(orig_handle,
                                                &num_elements) < 0:
                    _raise_from_odpi()
                if dpiVar_setNumElementsInArray(self._handle,
                                                num_elements) < 0:
                    _raise_from_odpi()
            for i in range(self.num_elements):
                source_data = &orig_data[i]
                if source_data.isNull:
                    continue
                if dpiVar_setFromBytes(self._handle, i,
                        source_data.value.asBytes.ptr,
                        source_data.value.asBytes.length) < 0:
                    _raise_from_odpi()
        finally:
            dpiVar_release(orig_handle)

    cdef int _set_cursor_value(self, object cursor, uint32_t pos) except -1:
        cdef:
            ThickCursorImpl cursor_impl = cursor._impl
            dpiData *data

        # if the cursor already has a handle, use it directly
        if cursor_impl._handle != NULL:
            if dpiVar_setFromStmt(self._handle, pos, cursor_impl._handle) < 0:
                _raise_from_odpi()

        # otherwise, make use of the statement handle allocated by the variable
        else:
            data = &self._data[pos]
            if dpiStmt_addRef(data.value.asStmt) < 0:
                _raise_from_odpi()
            cursor_impl._handle = data.value.asStmt
        cursor_impl._fixup_ref_cursor = True
        cursor.statement = None

    cdef int _set_num_elements_in_array(self, uint32_t num_elements) except -1:
        """
        Sets the number of elements in the array.
        """
        BaseVarImpl._set_num_elements_in_array(self, num_elements)
        if dpiVar_setNumElementsInArray(self._handle, num_elements) < 0:
            _raise_from_odpi()

    cdef int _set_scalar_value(self, uint32_t pos, object value) except -1:
        """
        Set the value of the variable at the given position. At this point it
        is assumed that all checks have been performed!
        """
        cdef:
            dpiDataBuffer temp_dbvalue
            dpiDataBuffer *dbvalue
            dpiBytes *as_bytes
            bint needs_set
            dpiData *data
        data = &self._data[pos]
        data.isNull = (value is None)
        if not data.isNull:
            if self._native_type_num == DPI_NATIVE_TYPE_STMT:
                self._set_cursor_value(value, pos)
            else:
                needs_set = self._native_type_num == DPI_NATIVE_TYPE_BYTES \
                        or (self._native_type_num == DPI_NATIVE_TYPE_LOB and \
                                not isinstance(value, PY_TYPE_LOB))
                if needs_set:
                    dbvalue = &temp_dbvalue
                else:
                    dbvalue = &data.value
                _convert_from_python(value, self.dbtype, self.objtype, dbvalue,
                                     self._buf, self, pos)
                if needs_set:
                    as_bytes = &dbvalue.asBytes
                    if dpiVar_setFromBytes(self._handle, pos, as_bytes.ptr,
                                           as_bytes.length) < 0:
                        _raise_from_odpi()

    cdef object _transform_array_to_python(self, uint32_t num_elements,
                                           dpiData *data):
        """
        Transforms an array from ODPI-C to a Python list.
        """
        cdef:
            object element_value
            list return_value
            uint32_t i
        return_value = cpython.PyList_New(num_elements)
        for i in range(num_elements):
            element_value = self._transform_element_to_python(i, data)
            cpython.Py_INCREF(element_value)
            cpython.PyList_SET_ITEM(return_value, i, element_value)
        return return_value

    cdef object _transform_element_to_python(self, uint32_t pos,
                                             dpiData *data):
        """
        Transforms a single element from the value supplied by ODPI-C to its
        equivalent Python value.
        """
        cdef:
            const char *encoding_errors = NULL
            bytes encoding_errors_bytes
            object value
        data = &data[pos]
        if not data.isNull:
            if self._native_type_num == DPI_NATIVE_TYPE_STMT:
                return self._get_cursor_value(&data.value)
            if self.encoding_errors is not None:
                encoding_errors_bytes = self.encoding_errors.encode()
                encoding_errors = encoding_errors_bytes
            value = _convert_to_python(self._conn_impl, self.dbtype,
                                       self.objtype, &data.value,
                                       self._preferred_num_type,
                                       self.bypass_decode, encoding_errors)
            if self.outconverter is not None:
                value = self.outconverter(value)
            return value
        elif self.convert_nulls:
            return self.outconverter(None)
