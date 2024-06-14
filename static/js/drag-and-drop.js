import DragDropManager from '@atlaskit/pragmatic-drag-and-drop';

document.addEventListener('DOMContentLoaded', function() {
  const manager = new DragDropManager();

  // 配置拖放源
  document.querySelectorAll('.item').forEach(item => {
    const source = {
      beginDrag: () => ({ id: item.dataset.id, name: item.dataset.name, price: item.dataset.price }),
    };
    manager.addSource(source, item);
  });

  // 配置放置目标
  const basket = document.getElementById('basket');
  const target = {
    canDrop: () => true,
    drop: (draggedItem) => {
      addToCart(draggedItem.name, draggedItem.id, draggedItem.price);
    }
  };
  manager.addTarget(target, basket);

  // 添加到购物车函数
  function addToCart(name, id, price) {
    const cartItems = document.getElementById('cart-items');
    let listItem = cartItems.querySelector(`[data-cart-id="${id}"]`);
    if (!listItem) {
      listItem = document.createElement('li');
      listItem.dataset.cartId = id; // 设置标记为购物车中的商品
      listItem.draggable = true;
      listItem.addEventListener('dragstart', function(event) {
        event.dataTransfer.setData('text/plain', JSON.stringify({ id, name, price }));
      });
      listItem.innerHTML = `${name} - €${price} x <span id="qty-${id}">1</span>
        <button onclick="changeQuantity('${id}', -1)">-</button>
        <button onclick="changeQuantity('${id}', 1)">+</button>`;
      listItem.className = 'cart-item';
      cartItems.appendChild(listItem);
    } else {
      changeQuantity(id, 1);
    }
  }

  // 更改数量函数
  window.changeQuantity = function(id, change) {
    const qtySpan = document.getElementById(`qty-${id}`);
    let qty = parseInt(qtySpan.textContent);
    qty += change;
    if (qty < 1) {
      removeFromCart(id);
    } else {
      qtySpan.textContent = qty;
    }
  }

  // 移除从购物车函数
  function removeFromCart(id) {
    const cartItems = document.getElementById('cart-items');
    const listItem = cartItems.querySelector(`[data-cart-id="${id}"]`);
    if (listItem) {
      cartItems.removeChild(listItem);
    }
  }
});
