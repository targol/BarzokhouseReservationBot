export interface FoodItem {
  id: string;
  title: string;
  description: string;
  price: string;
  availableMeals: ('lunch' | 'dinner')[];
}

export interface RoomItem {
  id: string;
  title: string;
  description: string;
  price: string;
  pricePerPerson: number;
  photo?: string;
}

export interface BookedRoomItem {
  roomId: string;
  title: string;
  pricePerPerson: number;
  adults: number;
  children5to12: number;
  childrenUnder5: number;
}

export interface FoodOrderItem {
  foodId: string;
  portions: number;
}

export interface FoodOrder {
  guestName: string;
  phone: string;
  roomTitle: string;
  date: string;
  weekday: string;
  meal: 'lunch' | 'dinner';
  items: FoodOrderItem[];
}
