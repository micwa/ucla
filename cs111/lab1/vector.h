#ifndef VECTOR_H_
#define VECTOR_H_

/* An array of void *, with a size and capacity. */
struct vector {
    int capacity;
    int size;
    void **objs;
};

void free_vector(struct vector *vec);
struct vector *make_vector(int capacity);
void vector_clear(struct vector *vec);
void *vector_get(const struct vector *vec, int index);
void *vector_back(struct vector *vec);
void *vector_pop(struct vector *vec);
void vector_push(struct vector *vec, void *obj);
void vector_remove(struct vector *vec, int index);

char **vector_to_words(struct vector *vec);

#endif /* VECTOR_H_ */
