# src/dishes/repository.py
from typing import Mapping, Any

from sqlalchemy import select, or_, desc, asc  #用于 构造一个查询对象（Select 对象）
from sqlalchemy.exc import IntegrityError

"""
AsyncSession 是 SQLAlchemy 在 异步环境（async / await） 中使用的数据库会话对象，
用来 管理一次数据库交互生命周期。
1.管理数据库连接（但不等于连接）
2.管理事务（最重要）
3.ORM 对象的“容器”和“跟踪器”
4.执行查询（ORM / Core）
5.控制对象生命周期（重要但容易忽略）
"""
from sqlalchemy.ext.asyncio import AsyncSession

from src.dishes.model import Dish

#仓库层
class DishRepository:
    """数据库表仓库层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dish_data: Mapping[str, Any]) -> Dish:
        dish = Dish(**dish_data)
        self.session.add(dish) #add()是session实例的一个方法，新增一条
        try:
            await self.session.commit()  #commit()是真正执行INSERT
        except IntegrityError:
            await self.session.rollback() #rollback()：把当前事务中，所有尚未 commit() 的数据库改动，全部撤销
            raise
        await self.session.refresh(dish)  #refresh()：重新从数据库查询一行数据，覆盖当前 ORM 对象的属性
        return dish

    async def get_by_id(self, dish_id: int) -> Dish | None:
        """使用 id 获取数据"""
        dish = await self.session.get(Dish, dish_id)
        if not dish:
            return None
        return dish

    async def get_all(
        self,
        *,
        search: str | None = None, #模糊查询关键字，用在name和description
        order_by: str = "id",
        direction: str = "asc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[Dish]:
        """获取所有数据"""
        query = select(Dish) #只是“搭 SQL”，还没查数据库


        # 1. 搜索
        if search:
            pattern = f"%{search}%" #
            #or_()把多个条件 用 SQL 的 OR 逻辑组合
            query = query.where(
                or_(Dish.name.ilike(pattern), Dish.description.ilike(pattern))
            )

        # 2. 排序
        allowed_sort = {"id", "name", "created_at"}
        if order_by not in allowed_sort:
            order_by = "id"
        order_column = getattr(Dish, order_by, Dish.id)
        query = query.order_by(
            desc(order_column) if direction == "desc" else asc(order_column)
        )

        # 3. 分页
        limit = min(limit, 500)
        offset = max(offset, 0)
        paginated_query = query.offset(offset).limit(limit)
        items = list(await self.session.scalars(paginated_query))

        return items

    async def update(self, dish_data: Mapping[str, Any], dish_id: int) -> Dish | None:
        """更新数据"""
        dish = await self.session.get(Dish, dish_id)
        if not dish:
            return None

        for key, value in dish_data.items():
            setattr(dish, key, value)
        await self.session.commit()
        await self.session.refresh(dish)
        return dish

    async def delete(self, dish_id: int) -> bool:
        """删除数据"""
        dish = await self.session.get(Dish, dish_id)
        if not dish:
            return False

        await self.session.delete(dish)
        await self.session.commit()
        return True
