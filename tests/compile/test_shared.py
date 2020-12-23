import numpy as np
import pytest

import theano
from theano.compile.sharedvalue import SharedVariable, generic, shared
from theano.tensor import Tensor, TensorType
from theano.utils import PYTHON_INT_BITWIDTH


class TestSharedVariable:
    def test_ctors(self):

        if PYTHON_INT_BITWIDTH == 32:
            assert shared(7).type == theano.tensor.iscalar, shared(7).type
        else:
            assert shared(7).type == theano.tensor.lscalar, shared(7).type
        assert shared(7.0).type == theano.tensor.dscalar
        assert shared(np.float32(7)).type == theano.tensor.fscalar

        # test tensor constructor
        b = shared(np.zeros((5, 5), dtype="int32"))
        assert b.type == TensorType("int32", broadcastable=[False, False])
        b = shared(np.random.rand(4, 5))
        assert b.type == TensorType("float64", broadcastable=[False, False])
        b = shared(np.random.rand(5, 1, 2))
        assert b.type == TensorType("float64", broadcastable=[False, False, False])

        assert shared([]).type == generic

        def badfunc():
            shared(7, bad_kw=False)

        with pytest.raises(TypeError):
            badfunc()

    def test_strict_generic(self):

        # this should work, because
        # generic can hold anything even when strict=True

        u = shared("asdf", strict=False)
        v = shared("asdf", strict=True)

        u.set_value(88)
        v.set_value(88)

    def test_create_numpy_strict_false(self):

        # here the value is perfect, and we're not strict about it,
        # so creation should work
        SharedVariable(
            name="u",
            type=Tensor(broadcastable=[False], dtype="float64"),
            value=np.asarray([1.0, 2.0]),
            strict=False,
        )

        # here the value is castable, and we're not strict about it,
        # so creation should work
        SharedVariable(
            name="u",
            type=Tensor(broadcastable=[False], dtype="float64"),
            value=[1.0, 2.0],
            strict=False,
        )

        # here the value is castable, and we're not strict about it,
        # so creation should work
        SharedVariable(
            name="u",
            type=Tensor(broadcastable=[False], dtype="float64"),
            value=[1, 2],  # different dtype and not a numpy array
            strict=False,
        )

        # here the value is not castable, and we're not strict about it,
        # this is beyond strictness, it must fail
        try:
            SharedVariable(
                name="u",
                type=Tensor(broadcastable=[False], dtype="float64"),
                value=dict(),  # not an array by any stretch
                strict=False,
            )
            assert 0
        except TypeError:
            pass

    def test_use_numpy_strict_false(self):

        # here the value is perfect, and we're not strict about it,
        # so creation should work
        u = SharedVariable(
            name="u",
            type=Tensor(broadcastable=[False], dtype="float64"),
            value=np.asarray([1.0, 2.0]),
            strict=False,
        )

        # check that assignments to value are cast properly
        u.set_value([3, 4])
        assert type(u.get_value()) is np.ndarray
        assert str(u.get_value(borrow=True).dtype) == "float64"
        assert np.all(u.get_value() == [3, 4])

        # check that assignments of nonsense fail
        try:
            u.set_value("adsf")
            assert 0
        except ValueError:
            pass

        # check that an assignment of a perfect value results in no copying
        uval = theano._asarray([5, 6, 7, 8], dtype="float64")
        u.set_value(uval, borrow=True)
        assert u.get_value(borrow=True) is uval

    def test_scalar_strict(self):
        def f(var, val):
            var.set_value(val)

        b = shared(np.int64(7), strict=True)
        assert b.type == theano.tensor.lscalar
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.int32(7), strict=True)
        assert b.type == theano.tensor.iscalar
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.int16(7), strict=True)
        assert b.type == theano.tensor.wscalar
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.int8(7), strict=True)
        assert b.type == theano.tensor.bscalar
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.float64(7.234), strict=True)
        assert b.type == theano.tensor.dscalar
        with pytest.raises(TypeError):
            f(b, 8)

        b = shared(np.float32(7.234), strict=True)
        assert b.type == theano.tensor.fscalar
        with pytest.raises(TypeError):
            f(b, 8)

        b = shared(np.float(7.234), strict=True)
        assert b.type == theano.tensor.dscalar
        with pytest.raises(TypeError):
            f(b, 8)

        b = shared(7.234, strict=True)
        assert b.type == theano.tensor.dscalar
        with pytest.raises(TypeError):
            f(b, 8)

        b = shared(np.zeros((5, 5), dtype="float32"))
        with pytest.raises(TypeError):
            f(b, np.random.rand(5, 5))

    def test_tensor_strict(self):
        def f(var, val):
            var.set_value(val)

        b = shared(np.int64([7]), strict=True)
        assert b.type == theano.tensor.lvector
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.int32([7]), strict=True)
        assert b.type == theano.tensor.ivector
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.int16([7]), strict=True)
        assert b.type == theano.tensor.wvector
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.int8([7]), strict=True)
        assert b.type == theano.tensor.bvector
        with pytest.raises(TypeError):
            f(b, 8.23)

        b = shared(np.float64([7.234]), strict=True)
        assert b.type == theano.tensor.dvector
        with pytest.raises(TypeError):
            f(b, 8)

        b = shared(np.float32([7.234]), strict=True)
        assert b.type == theano.tensor.fvector
        with pytest.raises(TypeError):
            f(b, 8)

        # np.float([7.234]) don't work
        #        b = shared(np.float([7.234]), strict=True)
        #        assert b.type == theano.tensor.dvector
        #        with pytest.raises(TypeError):
        #            f(b, 8)

        # This generate a generic type. Should we cast? I don't think.
        #        b = shared([7.234], strict=True)
        #        assert b.type == theano.tensor.dvector
        #        with pytest.raises(TypeError):
        #            f(b, 8)

        b = shared(np.zeros((5, 5), dtype="float32"))
        with pytest.raises(TypeError):
            f(b, np.random.rand(5, 5))

    def test_scalar_floatX(self):

        # the test should assure that floatX is not used in the shared
        # constructor for scalars Shared values can change, and since we don't
        # know the range they might take, we should keep the same
        # bit width / precision as the original value used to create the
        # shared variable.

        # Since downcasting of a value now raises an Exception,

        def f(var, val):
            var.set_value(val)

        b = shared(np.int64(7), allow_downcast=True)
        assert b.type == theano.tensor.lscalar
        f(b, 8.23)
        assert b.get_value() == 8

        b = shared(np.int32(7), allow_downcast=True)
        assert b.type == theano.tensor.iscalar
        f(b, 8.23)
        assert b.get_value() == 8

        b = shared(np.int16(7), allow_downcast=True)
        assert b.type == theano.tensor.wscalar
        f(b, 8.23)
        assert b.get_value() == 8

        b = shared(np.int8(7), allow_downcast=True)
        assert b.type == theano.tensor.bscalar
        f(b, 8.23)
        assert b.get_value() == 8

        b = shared(np.float64(7.234), allow_downcast=True)
        assert b.type == theano.tensor.dscalar
        f(b, 8)
        assert b.get_value() == 8

        b = shared(np.float32(7.234), allow_downcast=True)
        assert b.type == theano.tensor.fscalar
        f(b, 8)
        assert b.get_value() == 8

        b = shared(np.float(7.234), allow_downcast=True)
        assert b.type == theano.tensor.dscalar
        f(b, 8)
        assert b.get_value() == 8

        b = shared(7.234, allow_downcast=True)
        assert b.type == theano.tensor.dscalar
        f(b, 8)
        assert b.get_value() == 8

        b = shared(np.zeros((5, 5), dtype="float32"))
        with pytest.raises(TypeError):
            f(b, np.random.rand(5, 5))

    def test_tensor_floatX(self):
        def f(var, val):
            var.set_value(val)

        b = shared(np.int64([7]), allow_downcast=True)
        assert b.type == theano.tensor.lvector
        f(b, [8.23])
        assert b.get_value() == 8

        b = shared(np.int32([7]), allow_downcast=True)
        assert b.type == theano.tensor.ivector
        f(b, [8.23])
        assert b.get_value() == 8

        b = shared(np.int16([7]), allow_downcast=True)
        assert b.type == theano.tensor.wvector
        f(b, [8.23])
        assert b.get_value() == 8

        b = shared(np.int8([7]), allow_downcast=True)
        assert b.type == theano.tensor.bvector
        f(b, [8.23])
        assert b.get_value() == 8

        b = shared(np.float64([7.234]), allow_downcast=True)
        assert b.type == theano.tensor.dvector
        f(b, [8])
        assert b.get_value() == 8

        b = shared(np.float32([7.234]), allow_downcast=True)
        assert b.type == theano.tensor.fvector
        f(b, [8])
        assert b.get_value() == 8

        # np.float([7.234]) don't work
        #        b = shared(np.float([7.234]))
        #        assert b.type == theano.tensor.dvector
        #        f(b,[8])

        # This generate a generic type. Should we cast? I don't think.
        #        b = shared([7.234])
        #        assert b.type == theano.tensor.dvector
        #        f(b,[8])

        b = shared(np.asarray([7.234], dtype=theano.config.floatX), allow_downcast=True)
        assert b.dtype == theano.config.floatX
        f(b, [8])
        assert b.get_value() == 8

        b = shared(np.zeros((5, 5), dtype="float32"))
        with pytest.raises(TypeError):
            f(b, np.random.rand(5, 5))

    def test_err_symbolic_variable(self):
        with pytest.raises(TypeError):
            shared(theano.tensor.ones((2, 3)))
        shared(np.ones((2, 4)))