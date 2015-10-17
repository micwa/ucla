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
void *vector_back(struct vector *vec);
void *vector_pop(struct vector *vec);
void vector_push(struct vector *vec, void *obj);
char **vector_to_words(struct vector *vec);

#endif /* VECTOR_H_ */
