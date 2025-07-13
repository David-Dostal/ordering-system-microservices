from concurrent import futures
import grpc
import orders_pb2
import orders_pb2_grpc
from database import SessionLocal
from crud import get_user_orders

class OrderService(orders_pb2_grpc.OrderServiceServicer):

    def GetUserOrders(self, request, context):
        user_id = request.user_id
        db = SessionLocal()
        orders = get_user_orders(db, user_id=user_id)

        # Check if no orders are found
        if not orders:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('No orders found for the given user ID.')
            return orders_pb2.UserOrderResponse()

        # Convert the orders to gRPC messages
        grpc_orders = []
        for order in orders:
            grpc_items = [
                orders_pb2.OrderItem(
                    item_id=item.item_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price
                )
                for item in order.items
            ]

            grpc_order = orders_pb2.Order(
                id=order.id,
                user_id=order.user_id,
                total_price=order.total_price,
                address=order.address,
                items=grpc_items,
                order_date=order.order_date.isoformat() if order.order_date else None
            )
            grpc_orders.append(grpc_order)

        return orders_pb2.UserOrderResponse(orders=grpc_orders)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orders_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
