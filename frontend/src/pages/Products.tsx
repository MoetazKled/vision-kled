import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Product } from "../api";

export function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.products().then(setProducts).catch((err: Error) => setError(err.message));
  }, []);

  return (
    <>
      <h1>المنتجات</h1>
      <p className="lede">
        اختر منتجاً ثم أنشئ عميلاً مرتبطاً به. المحادثة تتغير حسب المنتج.
      </p>
      {error && <div className="error">{error}</div>}
      <div className="products">
        {products.map((product) => (
          <article className="card" key={product.slug}>
            <div className="tag">{product.slug}</div>
            <h2>{product.name_ar}</h2>
            <p>{product.audience}</p>
            <p>السعر: {product.price}</p>
            <p className="muted">الإعداد: {product.setup}</p>
            <Link className="btn accent" to={`/leads?product=${product.slug}`}>
              أنشئ عميلاً لهذا المنتج
            </Link>
          </article>
        ))}
      </div>
    </>
  );
}
