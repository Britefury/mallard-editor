from BritefuryJ.Live import LiveFunction

from Britefury.Util.LiveList import LiveList




class _ProjectedList (object):
	"""
	Projected list abstract interface that defines the `filter` and `map` methods
	"""
	def filter(self, fn):
		"""
		Create a filter projection of this list.

		:param fn: the filter function `fn(x) -> bool` that determines if an element is present
		 in the filtered list

		:return: a FilterProjectedList, that contains the elements in `self` for which `fn` returns True.
		Modifications to `self` are reflected in the filtered projection. Modifications to the filtered
		projection are applied to the underlying list (`self`)
		"""
		return FilterProjectedList(self, [fn])

	def map(self, fn, inv_fn):
		"""
		Create a map projection of this list. It contains the results of applying the function `fn`
		to each element in `self`.

		:param fn: the map function 'fn(x) -> y' that maps the element to its result
		:param inv_fn: the inverse map function 'inv_fn(y) -> x' that is the inverse of `fn`.

		:return: a MapProjectedList, that contains the result of applying `fn` to each element in `self`.
		The mapped projection is updated when `self` is modified. Modifying the mapped projection
		results in the changes being applied to the underlying list (`self`); the inverse map function
		`inv_fn` is used to convert these modifications.
		"""
		return MapProjectedList(self, [fn], [inv_fn])



class LiveProjectedList (LiveList, _ProjectedList):
	"""
	A live projected list

	A list that reports changes via the incremental computation system
	"""
	def __init__(self, xs=None):
		LiveList.__init__(self, xs)
		_ProjectedList.__init__(self)

		def _on_change(old_contents, new_contents):
			if self.__change_listener is not None:
				self.__change_listener()
		self.changeListener = _on_change

		self.__change_listener = None


	@property
	def change_listener(self):
		return self.__change_listener

	@change_listener.setter
	def change_listener(self, x):
		self.__change_listener = x






class FilterProjectedList (_ProjectedList):
	def __init__(self, underlying, filter_fns):
		self.__underlying = underlying
		self.__filter_fns = filter_fns

		def _apply():
			ii = zip(*[(i, x)   for i, x in enumerate(self.__underlying)   if self.__test(x)])
			if len(ii) == 2:
				return list(ii[0]), list(ii[1])
			else:
				return [], []
		self.__live = LiveFunction(_apply)

		def _live_listener(inc):
			if self.__change_listener is not None:
				self.__change_listener()

		self.__change_listener = None


	@property
	def change_listener(self):
		return self.__change_listener

	@change_listener.setter
	def change_listener(self, x):
		self.__change_listener = x


	def __test(self, item):
		for f in self.__filter_fns:
			if not f(item):
				return False
		return True

	@property
	def _indices_and_items(self):
		return self.__live.getValue()

	@property
	def _indices(self):
		return self.__live.getValue()[0]

	@property
	def _items(self):
		return self.__live.getValue()[1]


	def filter(self, fn):
		return FilterProjectedList(self.__underlying, self.__filter_fns + [fn])


	def __iter__(self):
		return iter(self._items)

	def __contains__(self, x):
		return x in self._items

	def __add__(self, xs):
		return self._items + xs

	def __mul__(self, x):
		return self._items * x

	def __rmul__(self, x):
		return x * self._items

	def __getitem__(self, index):
		return self._items[index]

	def __len__(self):
		return len(self._items)

	def index(self, x, i=None, j=None):
		if i is None:
			return self._items.index(x)
		elif j is None:
			return self._items.index(x, i)
		else:
			return self._items.index(x, i, j)

	def count(self, x):
		return self._items.count(x)

	def __setitem__(self, index, x):
		if isinstance(index, int)  or  isinstance(index, long):
			self.__underlying[self._indices[index]] = x
		else:
			indices = self._indices[index]
			for i, a in zip(indices, x):
				self.__underlying[i] = a
			if len(x) > len(indices):
				i = indices[-1] + 1   if len(indices) > 0  else len(self.__underlying)
				for a in x[len(indices):]:
					self.__underlying.insert(i, a)
					i += 1
			elif len(x) < len(indices):
				for i in reversed(indices[len(x):]):
					del self.__underlying[i]

	def __delitem__(self, index):
		if isinstance(index, int)  or  isinstance(index, long):
			del self.__underlying[self._indices[index]]
		else:
			indices = self._indices[index]
			for i in reversed(indices):
				del self.__underlying[i]

	def append(self, x):
		self.__underlying.append(x)

	def extend(self, xs):
		self.__underlying.extend(xs)

	def insert(self, i, x):
		indices = self._indices
		l = len(indices)
		i = min(max(i, -l), l-1)
		n = self._indices[i]
		self.__underlying.insert(n, x)

	def pop(self):
		i = self._indices[-1]
		x = self.__underlying[i]
		del self.__underlying[i]
		return x

	def remove(self, x):
		i = self._items.index( x )
		n = self._indices[i]
		del self.__underlying[n]

	def reverse(self):
		raise TypeError, 'Invalid operation'

	def sort(self, cmp=None, key=None, reverse=None):
		raise TypeError, 'Invalid operation'






class MapProjectedList (_ProjectedList):
	def __init__(self, underlying, map_fns, inverse_map_fns):
		self.__underlying = underlying
		self.__map_fns = map_fns
		self.__inverse_map_fns = inverse_map_fns

		def _apply():
			return [self.__apply(x)   for x in self.__underlying]
		self.__live = LiveFunction(_apply)

	def __apply(self, item):
		for m in self.__map_fns:
			item = m(item)
		return item

	def __inv_apply(self, item):
		for m in self.__inverse_map_fns:
			item = m(item)
		return item


	def map(self, fn, inv_fn):
		return MapProjectedList(self.__underlying, self.__map_fns + [fn], [inv_fn] + self.__inverse_map_fns)


	@property
	def _items(self):
		return self.__live.getValue()


	def __iter__(self):
		return iter(self._items)

	def __contains__(self, x):
		return x in self._items

	def __add__(self, xs):
		return self._items + xs

	def __mul__(self, x):
		return self._items * x

	def __rmul__(self, x):
		return x * self._items

	def __getitem__(self, index):
		return self._items[index]

	def __len__(self):
		return len(self._items)

	def index(self, x, i=None, j=None):
		if i is None:
			return self._items.index(x)
		elif j is None:
			return self._items.index(x, i)
		else:
			return self._items.index(x, i, j)

	def count(self, x):
		return self._items.count(x)

	def __setitem__(self, index, x):
		if isinstance(index, int)  or  isinstance(index, long):
			self.__underlying[index] = self.__inv_apply(x)
		else:
			self.__underlying[index] = [self.__inv_apply(a)   for a in x]

	def __delitem__(self, index):
		del self.__underlying[index]

	def append(self, x):
		self.__underlying.append(self.__inv_apply(x))

	def extend(self, xs):
		self.__underlying.extend([self.__inv_apply(x)   for x in xs])

	def insert(self, i, x):
		self.__underlying.insert(i, self.__inv_apply(x))

	def pop(self):
		x = self._items[-1]
		self.__underlying.pop()
		return x

	def remove(self, x):
		i = self._items.index(x)
		del self.__underlying[i]

	def reverse(self):
		raise TypeError, 'Invalid operation'

	def sort(self, cmp=None, key=None, reverse=None):
		raise TypeError, 'Invalid operation'




import unittest


class TestCase_FilterProjection (unittest.TestCase):
	def setUp(self):
		self.data = LiveProjectedList(range(0, 100, 10))
		self.filtered = self.data.filter(lambda x: x%20 == 0)

	def tearDown(self):
		self.filtered = None
		self.data = None


	def test_filter_q(self):
		self.assertEqual(self.filtered._indices_and_items, (range(0, 10, 2), range(0, 100, 20)))


	def test_iter(self):
		self.assertEqual(list(iter(self.filtered)), range(0, 100, 20))


	def test_contains(self):
		self.assertIn(40, self.filtered)
		self.assertNotIn(30, self.filtered)


	def test_add(self):
		self.assertEqual(self.filtered + [200], range(0, 100, 20) + [200])


	def test_mul(self):
		self.assertEqual(self.filtered * 2, range(0, 100, 20) * 2)
		self.assertEqual(2 * self.filtered, 2 * range(0, 100, 20))


	def test_getitem(self):
		self.assertEqual(self.filtered[2], 40)
		self.assertEqual(self.filtered[1:3], [20,40])


	def test_len(self):
		self.assertEqual(len(self.filtered), 5)


	def test_index(self):
		self.assertEqual(self.filtered.index(40), 2)
		self.assertEqual(self.filtered.index(80), 4)


	def test_count(self):
		self.assertEqual(self.filtered.count(20), 1)


	def test_setitem(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		self.filtered[2] = 200

		self.assertEqual(list(self.data), range(0, 40, 10) + [200] + range(50,100, 10))
		self.assertEqual(list(self.filtered), [0,20,200,60,80])


	def test_setitem_range(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		self.filtered[2:4] = [200,300]

		self.assertEqual(list(self.data), range(0, 40, 10) + [200] + [50] + [300] + range(70,100, 10))
		self.assertEqual(list(self.filtered), [0,20,200,300,80])


	def test_delitem(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		del self.filtered[2]

		self.assertEqual(list(self.data), range(0, 40, 10) + range(50, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,60,80])


	def test_delitem_range(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		del self.filtered[2:4]

		self.assertEqual(list(self.data), range(0, 40, 10) + [50] + range(70,100, 10))
		self.assertEqual(list(self.filtered), [0,20,80])


	def test_append(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		self.filtered.append(500)

		self.assertEqual(list(self.data), range(0, 100, 10) + [500])
		self.assertEqual(list(self.filtered), [0,20,40,60,80,500])

		self.filtered.append(505)

		self.assertEqual(list(self.data), range(0, 100, 10) + [500, 505])
		self.assertEqual(list(self.filtered), [0,20,40,60,80,500])


	def test_extend(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		self.filtered.extend([500, 505, 520])

		self.assertEqual(list(self.data), range(0, 100, 10) + [500, 505, 520])
		self.assertEqual(list(self.filtered), [0,20,40,60,80,500, 520])


	def test_insert(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		self.filtered.insert(2, 500)

		self.assertEqual(list(self.data), range(0, 40, 10) + [500] + range(40, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,500,40,60,80])


	def test_pop(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		x = self.filtered.pop()
		self.assertEqual(x, 80)

		self.assertEqual(list(self.data), range(0, 80, 10) + range(90, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60])


	def test_remove(self):
		self.assertEqual(list(self.data), range(0, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,40,60,80])

		self.filtered.remove(40)

		self.assertEqual(list(self.data), range(0, 40, 10) + range(50, 100, 10))
		self.assertEqual(list(self.filtered), [0,20,60,80])





class TestCase_MapProjection (unittest.TestCase):
	def setUp(self):
		self.data = LiveProjectedList(range(0,10,2))
		self.mapped = self.data.map(lambda x: x*10, lambda x: x/10)

	def tearDown(self):
		self.mapped = None
		self.data = None


	def test_iter(self):
		self.assertEqual(list(iter(self.mapped)), range(0, 100, 20))


	def test_contains(self):
		self.assertIn(40, self.mapped)
		self.assertNotIn(35, self.mapped)


	def test_add(self):
		self.assertEqual(self.mapped + [200], range(0, 100, 20) + [200])


	def test_mul(self):
		self.assertEqual(self.mapped * 2, range(0, 100, 20) * 2)
		self.assertEqual(2 * self.mapped, 2 * range(0, 100, 20))


	def test_getitem(self):
		self.assertEqual(self.mapped[2], 40)
		self.assertEqual(self.mapped[1:3], [20,40])


	def test_len(self):
		self.assertEqual(len(self.mapped), 5)


	def test_index(self):
		self.assertEqual(self.mapped.index(40), 2)
		self.assertEqual(self.mapped.index(80), 4)


	def test_count(self):
		self.assertEqual(self.mapped.count(20), 1)


	def test_setitem(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		self.mapped[2] = 200

		self.assertEqual(list(self.data), [0, 2, 20, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,200,60,80])


	def test_setitem_range(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		self.mapped[2:4] = [200,300]

		self.assertEqual(list(self.data),[0, 2, 20, 30, 8])
		self.assertEqual(list(self.mapped), [0,20,200,300,80])


	def test_delitem(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		del self.mapped[2]

		self.assertEqual(list(self.data), [0, 2, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,60,80])


	def test_delitem_range(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		del self.mapped[2:4]

		self.assertEqual(list(self.data), [0, 2, 8])
		self.assertEqual(list(self.mapped), [0,20,80])


	def test_append(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		self.mapped.append(500)

		self.assertEqual(list(self.data), [0, 2, 4, 6, 8, 50])
		self.assertEqual(list(self.mapped), [0,20,40,60,80, 500])

		self.mapped.append(505)

		self.assertEqual(list(self.data), [0, 2, 4, 6, 8, 50, 50])
		self.assertEqual(list(self.mapped), [0,20,40,60,80, 500, 500])


	def test_extend(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		self.mapped.extend([500, 505, 520])

		self.assertEqual(list(self.data), [0, 2, 4, 6, 8, 50, 50, 52])
		self.assertEqual(list(self.mapped), [0,20,40,60,80,500,500,520])


	def test_insert(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		self.mapped.insert(2, 500)

		self.assertEqual(list(self.data), [0, 2, 50, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,500,40,60,80])


	def test_pop(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		x = self.mapped.pop()
		self.assertEqual(x, 80)

		self.assertEqual(list(self.data), [0, 2, 4, 6])
		self.assertEqual(list(self.mapped), [0,20,40,60])


	def test_remove(self):
		self.assertEqual(list(self.data), [0, 2, 4, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,40,60,80])

		self.mapped.remove(40)

		self.assertEqual(list(self.data), [0, 2, 6, 8])
		self.assertEqual(list(self.mapped), [0,20,60,80])
